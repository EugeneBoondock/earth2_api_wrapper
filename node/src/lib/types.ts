export type Earth2AuthOptions = {
  email?: string;
  password?: string;
  cookieJar?: string;
  csrfToken?: string;
};

export type LeaderboardQuery = Record<string, string | number | boolean | undefined> & {
  sort_by?: string;
  country?: string;
  continent?: string;
};

export interface MarketSearchQuery {
  country?: string;
  landfieldTier?: string | number;
  tileClass?: string | number;
  tileCount?: string | number;
  page?: number;
  items?: number;
  search?: string;
  searchTerms?: string[];
}

export interface MarketItemSimplified {
  id: string;
  description?: string | null;
  location?: string | null;
  country?: string | null;
  tier?: number | string | null;
  tileClass?: number | string | null;
  tileCount?: number | null;
  price?: number | null;
  ppt?: number | null;
  thumbnail?: string | null;
}

export interface TrendingPlace {
  id: string;
  tier: number | null;
  placeCode: string | null;
  placeName: string | null;
  tilesSold: number | null;
  tilePrice: number | null;
  timeframeDays: number | null;
  country: string | null;
  center: [number, number] | null;
}

export interface ResourcesResponse {
  data: Array<{
    id: string;
    type: 'resources';
    attributes: {
      size: number;
      category: string;
      stats?: unknown;
      max?: number | null;
      m3?: number | null;
    };
  }>;
  sources?: Array<{ title: string; url: string }>;
}

export interface AvatarSale {
  id: string;
  skinName?: string | null;
  price?: number | null;
  buyer?: string | null;
  seller?: string | null;
  soldAt?: string | null;
}

export interface UserInfo {
  id: string;
  username?: string | null;
  avatar?: string | null;
  created?: string | null;
  properties?: number | null;
  followers?: number | null;
  following?: number | null;
  country?: string | null;
  verified?: boolean;
}

export interface Favorite {
  id: string;
  landfieldId: string;
  description: string;
  location: string;
}


