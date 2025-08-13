import { LeaderboardQuery, MarketItemSimplified, MarketSearchQuery, ResourcesResponse, TrendingPlace, UserInfo, Favorite } from './types.js';

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

  // Helper to normalize Earth2's quirky OAuth URLs
  private normalizeAuthUrl(raw: string): string {
    let url = raw;
    if (url.startsWith('/')) {
      url = `https://auth.earth2.io${url}`;
    } else if (!url.startsWith('http')) {
      url = `https://auth.earth2.io/${url}`;
    }
    // Replace illegal psid: with psid=
    url = url.replace('psid:', 'psid=');
    return encodeURI(url);
  }

  // Authenticate with email/password using Earth2's Kinde OAuth flow
  async authenticate(email: string, password: string): Promise<{ success: boolean; message: string }> {
    try {
      const userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';
      let allCookies: string[] = [];

      // Step 1: Start OAuth flow by visiting the main login page
      const loginPageResponse = await this.fetchImpl('https://app.earth2.io/login', {
        method: 'GET',
        headers: {
          'User-Agent': userAgent,
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
          'Accept-Language': 'en-US,en;q=0.5',
          'Accept-Encoding': 'gzip, deflate, br',
          'Connection': 'keep-alive',
          'Upgrade-Insecure-Requests': '1',
        },
        redirect: 'manual'
      });

      const loginCookies = loginPageResponse.headers.get('set-cookie');
      if (loginCookies) allCookies.push(loginCookies);

      // Step 2: Handle the first redirect (301 to /login/)
      let locationHeader = loginPageResponse.headers.get('location');
      if (!locationHeader) {
        return { success: false, message: 'No redirect found from login page' };
      }

      if (locationHeader.startsWith('/')) {
        locationHeader = `https://app.earth2.io${locationHeader}`;
      }

      const step2Response = await this.fetchImpl(locationHeader, {
        method: 'GET',
        headers: {
          'User-Agent': userAgent,
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
          'Accept-Language': 'en-US,en;q=0.5',
          'Cookie': allCookies.join('; '),
        },
        redirect: 'manual'
      });

      const step2Cookies = step2Response.headers.get('set-cookie');
      if (step2Cookies) allCookies.push(step2Cookies);

      // Step 3: Follow the OAuth redirect (302 to auth.earth2.io)
      const oauthUrl = step2Response.headers.get('location');
      if (!oauthUrl) {
        return { success: false, message: 'No OAuth redirect found from /login/ page' };
      }

      const oauthResponse = await this.fetchImpl(oauthUrl, {
        method: 'GET',
        headers: {
          'User-Agent': userAgent,
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
          'Accept-Language': 'en-US,en;q=0.5',
          'Cookie': allCookies.join('; '),
        },
        redirect: 'manual'
      });

      const oauthCookies = oauthResponse.headers.get('set-cookie');
      if (oauthCookies) allCookies.push(oauthCookies);

      // Step 4: Follow redirects to get to the email form
      let currentResponse = oauthResponse;
      let redirectCount = 0;
      while (currentResponse.status >= 300 && currentResponse.status < 400 && redirectCount < 5) {
        const nextUrlRaw = currentResponse.headers.get('location');
        if (!nextUrlRaw) break;
        const nextUrl = this.normalizeAuthUrl(nextUrlRaw);
        
        currentResponse = await this.fetchImpl(nextUrl, {
          method: 'GET',
          headers: {
            'User-Agent': userAgent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Cookie': allCookies.join('; '),
          },
          redirect: 'manual'
        });

        const redirectCookies = currentResponse.headers.get('set-cookie');
        if (redirectCookies) allCookies.push(redirectCookies);
        redirectCount++;
      }

      // Step 5: Extract and submit email form
      const emailPageHtml = await currentResponse.text();
      let emailFormAction = currentResponse.url;
      
      const formMatch = emailPageHtml.match(/<form[^>]*action=['"](.*?)['"][^>]*>/);
      if (formMatch) {
        emailFormAction = this.normalizeAuthUrl(formMatch[1]);
      }

      // Extract hidden fields
      const hiddenInputs = emailPageHtml.match(/<input[^>]*type=['"](hidden|csrf)['"][^>]*>/g) || [];
      const formData = [`email=${encodeURIComponent(email)}`];
      
      for (const input of hiddenInputs) {
        const nameMatch = input.match(/name=['"](.*?)['"]/);
        const valueMatch = input.match(/value=['"](.*?)['"]/);
        if (nameMatch && valueMatch) {
          formData.push(`${encodeURIComponent(nameMatch[1])}=${encodeURIComponent(valueMatch[1])}`);
        }
      }

      const emailResponse = await this.fetchImpl(emailFormAction, {
        method: 'POST',
        headers: {
          'User-Agent': userAgent,
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
          'Accept-Language': 'en-US,en;q=0.5',
          'Content-Type': 'application/x-www-form-urlencoded',
          'Origin': 'https://auth.earth2.io',
          'Referer': currentResponse.url,
          'Cookie': allCookies.join('; '),
        },
        body: formData.join('&'),
        redirect: 'manual'
      });

      const emailCookies = emailResponse.headers.get('set-cookie');
      if (emailCookies) allCookies.push(emailCookies);

      // Step 6: Follow redirects to password page
      let passwordPageResponse = emailResponse;
      redirectCount = 0;
      while (passwordPageResponse.status >= 300 && passwordPageResponse.status < 400 && redirectCount < 5) {
        const nextUrlRaw = passwordPageResponse.headers.get('location');
        if (!nextUrlRaw) break;
        const nextUrl = this.normalizeAuthUrl(nextUrlRaw);
        
        passwordPageResponse = await this.fetchImpl(nextUrl, {
          method: 'GET',
          headers: {
            'User-Agent': userAgent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Cookie': allCookies.join('; '),
          },
          redirect: 'manual'
        });

        const passwordRedirectCookies = passwordPageResponse.headers.get('set-cookie');
        if (passwordRedirectCookies) allCookies.push(passwordRedirectCookies);
        redirectCount++;
      }

      // Step 7: Extract and submit password form
      const passwordPageHtml = await passwordPageResponse.text();
      let passwordFormAction = passwordPageResponse.url;
      
      const passwordFormMatch = passwordPageHtml.match(/<form[^>]*action=['"](.*?)['"][^>]*>/);
      if (passwordFormMatch) {
        passwordFormAction = this.normalizeAuthUrl(passwordFormMatch[1]);
      }

      const passwordHiddenInputs = passwordPageHtml.match(/<input[^>]*type=['"](hidden|csrf)['"][^>]*>/g) || [];
      const passwordFormData = [`password=${encodeURIComponent(password)}`];
      
      for (const input of passwordHiddenInputs) {
        const nameMatch = input.match(/name=['"](.*?)['"]/);
        const valueMatch = input.match(/value=['"](.*?)['"]/);
        if (nameMatch && valueMatch) {
          passwordFormData.push(`${encodeURIComponent(nameMatch[1])}=${encodeURIComponent(valueMatch[1])}`);
        }
      }

      const passwordResponse = await this.fetchImpl(passwordFormAction, {
        method: 'POST',
        headers: {
          'User-Agent': userAgent,
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
          'Accept-Language': 'en-US,en;q=0.5',
          'Content-Type': 'application/x-www-form-urlencoded',
          'Origin': 'https://auth.earth2.io',
          'Referer': passwordPageResponse.url,
          'Cookie': allCookies.join('; '),
        },
        body: passwordFormData.join('&'),
        redirect: 'manual'
      });

      const passwordCookies = passwordResponse.headers.get('set-cookie');
      if (passwordCookies) allCookies.push(passwordCookies);

      // Step 8: Follow OAuth callback chain back to app.earth2.io
      let currentUrl = passwordResponse.headers.get('location');
      redirectCount = 0;
      while (currentUrl && redirectCount < 10) {
        if (currentUrl.startsWith('/')) {
          currentUrl = `https://app.earth2.io${currentUrl}`;
        }
        
        const redirectResponse = await this.fetchImpl(currentUrl, {
          method: 'GET',
          headers: {
            'User-Agent': userAgent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Cookie': allCookies.join('; '),
          },
          redirect: 'manual'
        });

        const redirectCookies = redirectResponse.headers.get('set-cookie');
        if (redirectCookies) allCookies.push(redirectCookies);

        currentUrl = redirectResponse.headers.get('location');
        redirectCount++;

        if (currentUrl && currentUrl.includes('app.earth2.io')) {
          break;
        }
      }

      if (redirectCount >= 10) {
        return { success: false, message: 'Too many redirects during OAuth flow' };
      }

      // Store final cookies
      this.cookieJar = allCookies.join('; ');
      
      return { 
        success: true, 
        message: 'Authentication successful! OAuth flow completed and cookies have been set.' 
      };

    } catch (error) {
      return { 
        success: false, 
        message: `Authentication error: ${error instanceof Error ? error.message : String(error)}` 
      };
    }
  }

  // Check if current session is still valid
  async checkSessionValidity(): Promise<{ isValid: boolean; needsReauth: boolean }> {
    if (!this.cookieJar) {
      return { isValid: false, needsReauth: true };
    }

    try {
      // Test session by calling a simple endpoint
      const testResponse = await this.fetchImpl('https://r.earth2.io/avatar_sales?page=1&perPage=12', {
        method: 'GET',
        headers: {
          'User-Agent': 'earth2-api-wrapper/0.1 (+https://npmjs.com/package/earth2-api-wrapper)',
          'Accept': 'application/json, text/plain, */*',
          'Cookie': this.cookieJar,
          'Referer': 'https://app.earth2.io/',
          'Origin': 'https://app.earth2.io'
        }
      });

      if (testResponse.status === 401 || testResponse.status === 403) {
        return { isValid: false, needsReauth: true };
      }

      return { isValid: true, needsReauth: false };

    } catch (error) {
      return { isValid: false, needsReauth: true };
    }
  }

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
    }).filter((x: MarketItemSimplified) => x.ppt !== null).sort((a: MarketItemSimplified, b: MarketItemSimplified) => (a.ppt! - b.ppt!));
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


