export interface Stock {
  ticker: string;
  name: string;
  sector: string;
  subsector: string;
  indexes: string[];
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  marketCap: number;
  pe: number | null;
  pb: number | null;
  roe: number | null;
  netMargin: number | null;
  dividendYield: number | null;
}

export interface StocksData {
  updatedAt: string;
  count: number;
  stocks: Stock[];
}

export interface MarketData {
  updatedAt: string;
  bist100: { value: number; change: number; changePercent: number };
  usdTry: { value: number; change: number; changePercent: number };
  eurTry: { value: number; change: number; changePercent: number };
}

export interface Sector {
  slug: string;
  name: string;
  stockCount: number;
  avgPE: number | null;
  avgPB: number | null;
  avgROE: number | null;
  performance: number;
}

export interface CompanyDetail {
  ticker: string;
  name: string;
  sector: string;
  subsector: string;
  indexes: string[];
  website: string;
  capital: number;
  freeFloat: number;
  ipoDate: string;
  price: {
    last: number;
    change: number;
    changePercent: number;
    open: number;
    high: number;
    low: number;
    volume: number;
    marketCap: number;
    updatedAt: string;
  };
  ratios: Ratios;
}

export interface Ratios {
  pe: number | null;
  pb: number | null;
  ps: number | null;
  evEbitda: number | null;
  roe: number | null;
  roa: number | null;
  netMargin: number | null;
  grossMargin: number | null;
  ebitdaMargin: number | null;
  currentRatio: number | null;
  quickRatio: number | null;
  debtEquity: number | null;
  netDebtEbitda: number | null;
  revenueGrowthYoy: number | null;
  netIncomeGrowthYoy: number | null;
  equityGrowthYoy: number | null;
}

export interface FinancialData {
  ticker: string;
  currency: string;
  periods: string[];
  balanceSheet: {
    currentAssets: number[];
    nonCurrentAssets: number[];
    totalAssets: number[];
    currentLiabilities: number[];
    nonCurrentLiabilities: number[];
    totalLiabilities: number[];
    equity: number[];
  };
  incomeStatement: {
    revenue: number[];
    costOfRevenue: number[];
    grossProfit: number[];
    operatingIncome: number[];
    netIncome: number[];
    ebitda: number[];
  };
  cashFlow: {
    operating: number[];
    investing: number[];
    financing: number[];
  };
}

export interface PricePoint {
  date: string;
  close: number;
  volume: number;
}
