import { LeaderboardQuery, MarketItemSimplified, MarketSearchQuery, ResourcesResponse, TrendingPlace } from './types';

type FetchLike = (url: string, init?: any) => Promise<any>;

export class Earth2Client {
  private fetchImpl: FetchLike;
  private cookieJar?: string;
  private csrfToken?: string;

  constructor(options?: { fetch?: FetchLike; cookieJar?: string; csrfToken?: string }) {
    this.fetchImpl = options?.fetch || fetch;
    this.cookieJar = options?.cookieJar;
    this.csrfToken = options?.csrfToken;
  }

  setCookieJar(jar: string | undefined) { this.cookieJar = jar; }
  setCsrfToken(token: string | undefined) { this.csrfToken = token; }

  // Public GET helper to r.earth2.io (session optional; many endpoints are public)
  private async getJson<T>(url: string, init?: any): Promise<T> {
    const headers: Record<string, string> = {
      Accept: 'application/json, text/plain, */*',
      'User-Agent': 'earth2-api-wrapper/0.1 (+https://npmjs.com/package/earth2-api-wrapper)'
    };
    if (this.cookieJar) headers['Cookie'] = this.cookieJar;
    if (this.csrfToken) {
      headers['X-CSRF-TOKEN'] = this.csrfToken;
      headers['X-XSRF-TOKEN'] = this.csrfToken;
      headers['X-CsrfToken'] = this.csrfToken;
    }
    const res = await this.fetchImpl(url, { ...init, headers: { ...(init?.headers as any), ...headers }, method: 'GET' });
    if (!res.ok) {
      const text = await res.text().catch(() => '');
      throw new Error(`GET ${url} failed: ${res.status} ${text?.slice(0, 200)}`);
    }
    return res.json() as Promise<T>;
  }

  // Public GET that may return HTML; used by marketplace floor discovery
  private async getText(url: string): Promise<string> {
    const headers: Record<string, string> = {
      Accept: 'application/json, text/plain, */*',
      'User-Agent': 'earth2-api-wrapper/0.1 (+https://npmjs.com/package/earth2-api-wrapper)'
    };
    if (this.cookieJar) headers['Cookie'] = this.cookieJar;
    if (this.csrfToken) {
      headers['X-CSRF-TOKEN'] = this.csrfToken;
      headers['X-XSRF-TOKEN'] = this.csrfToken;
      headers['X-CsrfToken'] = this.csrfToken;
    }
    const res = await this.fetchImpl(url, { headers });
    if (!res.ok) {
      const t = await res.text().catch(() => '');
      throw new Error(`GET ${url} failed: ${res.status} ${t?.slice(0, 200)}`);
    }
    return res.text();
  }

  // Landing metrics
  async getLandingMetrics(): Promise<any> {
    return this.getJson('https://r.earth2.io/landing/metrics');
  }

  // Trending places
  async getTrendingPlaces(): Promise<{ data: TrendingPlace[] }> {
    const j = await this.getJson<any>('https://r.earth2.io/landing/trending_places');
    const data = Array.isArray(j?.data) ? j.data : [];
    const normalized: TrendingPlace[] = data.map((item: any) => {
      const a = item?.attributes || {};
      return {
        id: item?.id,
        tier: a?.landfieldTier ?? null,
        placeCode: a?.placeCode ?? null,
        placeName: a?.placeName ?? null,
        tilesSold: a?.tilesSold ?? null,
        tilePrice: a?.tilePrice ?? null,
        timeframeDays: a?.timeframeDays ?? null,
        country: a?.country ?? null,
        center: a?.center ?? null,
      } as TrendingPlace;
    });
    return { data: normalized };
  }

  // Territory release winners
  async getTerritoryReleaseWinners(): Promise<{ data: any[] }> {
    const j = await this.getJson<any>('https://r.earth2.io/landing/territory_release_winners');
    const data = Array.isArray(j?.data) ? j.data : [];
    const normalized = data.map((item: any) => {
      const a = item?.attributes || {};
      return {
        id: item?.id,
        territoryCode: a?.territoryCode ?? null,
        territoryName: a?.territoryName ?? null,
        country: a?.country ?? null,
        countryName: a?.countryName ?? null,
        votesValue: a?.votesValue ?? null,
        votesT1: a?.votesT1 ?? null,
        votesT2: a?.votesT2 ?? null,
        votesEsnc: a?.votesEsnc ?? null,
        releaseAt: a?.releaseAt ?? null,
        center: a?.center ?? null,
      };
    });
    return { data: normalized };
  }

  // Single property details (public)
  async getProperty(id: string): Promise<any> {
    if (!id) throw new Error('id required');
    return this.getJson(`https://r.earth2.io/landfields/${encodeURIComponent(id)}`);
  }

  // Market search (r.earth2.io/marketplace). Returns Earth2 raw plus simplified list
  async searchMarket(query: MarketSearchQuery): Promise<{ raw: any; items: MarketItemSimplified[]; count: number }>{
    const url = new URL('https://r.earth2.io/marketplace');
    if (query.country) url.searchParams.set('country', String(query.country));
    if (query.items) url.searchParams.set('items', String(query.items));
    if (query.page) url.searchParams.set('page', String(query.page));
    if (query.search) url.searchParams.set('search', String(query.search));
    url.searchParams.set('sorting', 'price_per_tile');
    if (query.landfieldTier != null) url.searchParams.set('landfieldTier', String(query.landfieldTier));
    if (query.tileClass != null && String(query.landfieldTier) === '1') url.searchParams.set('tileClass', String(query.tileClass));
    if (query.tileCount != null) url.searchParams.set('tileCount', String(query.tileCount));
    for (const term of query.searchTerms || []) url.searchParams.append('searchTerms[]', term);

    const json = await this.getJson<any>(url.toString());
    const landfields = Array.isArray(json?.landfields) ? json.landfields : [];
    const items: MarketItemSimplified[] = landfields.map((lf: any) => {
      const ppt = lf.tileCount > 0 && lf.price ? lf.price / lf.tileCount : null;
      return {
        id: lf.id,
        description: lf.description,
        location: lf.location,
        country: lf.country,
        tier: lf.landfieldTier,
        tileClass: lf.tileClass,
        tileCount: lf.tileCount,
        price: lf.price,
        ppt,
        thumbnail: lf.thumbnail,
      } as MarketItemSimplified;
    }).filter(x => x.ppt !== null).sort((a, b) => (a.ppt! - b.ppt!));
    return { raw: json, items, count: Number(json?.count || 0) };
  }

  // Marketplace minimal floor extraction (if JSON structure changes). Not guaranteed; fallback uses HTML heuristic
  async getMarketFloor(params: { country?: string; landfieldTier?: string; tileCount?: string; tileClass?: string }): Promise<{ ppt: number; source: 'json' | 'html' } | null> {
    const url = new URL('https://r.earth2.io/marketplace');
    if (params.country) url.searchParams.set('country', params.country);
    url.searchParams.set('items', '24');
    url.searchParams.set('page', '1');
    url.searchParams.set('search', '');
    url.searchParams.set('sorting', 'price_per_tile');
    if (params.tileCount) url.searchParams.set('tileCount', params.tileCount);
    if (params.landfieldTier) url.searchParams.set('landfieldTier', params.landfieldTier);
    if (params.tileClass && params.landfieldTier === '1') url.searchParams.set('tileClass', params.tileClass);

    const text = await this.getText(url.toString());
    try {
      const json = JSON.parse(text);
      if (json && Array.isArray(json.landfields)) {
        let min = Number.POSITIVE_INFINITY;
        for (const p of json.landfields) {
          const ppt = p?.price && p?.tileCount ? p.price / p.tileCount : null;
          if (ppt && ppt > 0) min = Math.min(min, ppt);
        }
        if (Number.isFinite(min)) return { ppt: min, source: 'json' };
      }
    } catch {}
    const pptHtml = this.parsePerTile(text);
    return pptHtml ? { ppt: pptHtml, source: 'html' } : null;
  }

  private parsePerTile(html: string): number | null {
    const patterns = [
      /\(\s*([0-9]+[0-9.,]*)\s*per\s*tile\s*\)/gi,
      /([0-9]+[0-9.,]*)\s*per\s*tile/gi,
      /[€$£¥]\s*([0-9]+[0-9.,]*)\s*per\s*tile/gi,
      />\s*([0-9]+[0-9.,]*)\s*per\s*tile\s*</gi,
      /"price[_\-]?per[_\-]?tile":\s*([0-9]+[0-9.,]*)/gi,
    ];
    let min = Number.POSITIVE_INFINITY;
    for (const pattern of patterns) {
      let m: RegExpExecArray | null;
      while ((m = pattern.exec(html))) {
        const val = parseFloat(m[1].replace(/,/g, ''));
        if (!Number.isNaN(val) && val > 0) min = Math.min(min, val);
      }
    }
    return Number.isFinite(min) ? min : null;
  }

  // Leaderboards
  async getLeaderboardPlayers(params: LeaderboardQuery): Promise<any> {
    const url = new URL('https://r.earth2.io/leaderboards/players');
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null) url.searchParams.append(k, String(v));
    });
    return this.getJson(url.toString());
  }

  async getLeaderboardCountries(params: LeaderboardQuery): Promise<any> {
    const url = new URL('https://r.earth2.io/leaderboards/landfield_countries');
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null) url.searchParams.append(k, String(v));
    });
    return this.getJson(url.toString());
  }

  async getLeaderboardPlayerCountries(params: LeaderboardQuery): Promise<any> {
    const url = new URL('https://r.earth2.io/leaderboards/player_countries');
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null) url.searchParams.append(k, String(v));
    });
    return this.getJson(url.toString());
  }

  // Resources API (requires propertyId). If upstream fails, there is no CSV fallback here; consumers can add their own fallback.
  async getResources(propertyId: string): Promise<ResourcesResponse> {
    if (!propertyId) throw new Error('propertyId required');
    const url = `https://resources.earth2.io/v1/landfields/${encodeURIComponent(propertyId)}/resources`;
    return this.getJson<ResourcesResponse>(url);
  }

  // Avatar sales
  async getAvatarSales(): Promise<{ data: any[] }> {
    return this.getJson('https://r.earth2.io/avatar_sales');
  }

  // User info
  async getUserInfo(userId: string): Promise<{ data: UserInfo }> {
    return this.getJson(`https://app.earth2.io/api/v2/user_info/${userId}`);
  }

  // Bulk user info
  async getUsers(userIds: string[]): Promise<{ data: UserInfo[] }> {
    const params = new URLSearchParams();
    userIds.forEach(id => params.append('ids', id));
    return this.getJson(`https://app.earth2.io/users?${params.toString()}`);
  }

  // User favorites (requires auth)
  async getMyFavorites(): Promise<{ data: Favorite[] }> {
    return this.getJson('https://r.earth2.io/api/v2/my/favorites');
  }
}


