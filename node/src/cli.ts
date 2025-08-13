#!/usr/bin/env node
import { Command } from 'commander';
import chalk from 'chalk';
import Table from 'cli-table3';
import { Earth2Client } from './lib/client.js';

const program = new Command();
program
  .name('e2')
  .description('Earth2 API CLI (unofficial)')
  .version('0.2.0');

// Helper functions for formatting
function formatTable(headers: string[], rows: any[][]): string {
  const table = new Table({
    head: headers.map(h => chalk.cyan.bold(h)),
    style: { border: ['grey'] }
  });
  rows.forEach(row => table.push(row));
  return table.toString();
}

function formatPrice(price: number): string {
  return chalk.green(`$${price.toLocaleString()}`);
}

function formatNumber(num: number): string {
  return chalk.yellow(num.toLocaleString());
}

function logSuccess(message: string): void {
  console.log(chalk.green('✓'), message);
}

function logError(message: string): void {
  console.log(chalk.red('✗'), message);
}

function logInfo(message: string): void {
  console.log(chalk.blue('ℹ'), message);
}

program
  .command('login')
  .description('Authenticate with Earth2 using Kinde OAuth flow')
  .option('-e, --email <email>', 'Email address')
  .option('-p, --password <password>', 'Password')
  .action(async (opts) => {
    const client = new Earth2Client();
    const email = opts.email || process.env.E2_EMAIL;
    const password = opts.password || process.env.E2_PASSWORD;
    
    if (!email || !password) {
      logError('Email and password are required. Use --email and --password or set E2_EMAIL and E2_PASSWORD environment variables.');
      process.exit(1);
    }
    
    logInfo('Starting Earth2 Kinde OAuth authentication flow...');
    logInfo('This may take a moment as we navigate through multiple redirects...');
    
    const result = await client.authenticate(email, password);
    
    if (result.success) {
      logSuccess(result.message);
      logInfo('Session cookies have been stored for this session.');
      logInfo('You can now use authenticated endpoints like "e2 my-favorites"');
      
      // Test the session
      logInfo('Testing session validity...');
      const sessionCheck = await client.checkSessionValidity();
      if (sessionCheck.isValid) {
        logSuccess('Session is valid and ready to use!');
      } else {
        logError('Session validation failed. You may need to try again.');
      }
    } else {
      logError(result.message);
      logError('OAuth authentication failed. Please check your credentials and try again.');
      process.exit(1);
    }
  });

program
  .command('check-session')
  .description('Check if current session is still valid')
  .action(async () => {
    const client = new Earth2Client({ cookieJar: process.env.E2_COOKIE, csrfToken: process.env.E2_CSRF });
    
    if (!client['cookieJar']) {
      logError('No session found. Please run "e2 login" first.');
      process.exit(1);
    }
    
    logInfo('Checking session validity...');
    const result = await client.checkSessionValidity();
    
    if (result.isValid) {
      logSuccess('Session is valid!');
    } else {
      logError('Session is invalid or expired.');
      if (result.needsReauth) {
        logInfo('Please run "e2 login" to re-authenticate.');
      }
      process.exit(1);
    }
  });

program
  .command('trending')
  .description('Get trending places')
  .option('--json', 'Output raw JSON')
  .action(async (opts) => {
    const client = new Earth2Client({ cookieJar: process.env.E2_COOKIE, csrfToken: process.env.E2_CSRF });
    const res = await client.getTrendingPlaces();
    
    if (opts.json) {
      console.log(JSON.stringify(res, null, 2));
      return;
    }
    
    console.log(chalk.bold.blue('\n🌍 Trending Places\n'));
    
    if (res.data.length === 0) {
      logInfo('No trending places found');
      return;
    }
    
    const table = formatTable(
      ['Place', 'Country', 'Tier', 'Tiles Sold', 'Tile Price', 'Days'],
      res.data.map(place => [
        place.placeName || 'N/A',
        place.country || 'N/A',
        place.tier ? `T${place.tier}` : 'N/A',
        place.tilesSold ? formatNumber(place.tilesSold) : 'N/A',
        place.tilePrice ? formatPrice(place.tilePrice) : 'N/A',
        place.timeframeDays ? formatNumber(place.timeframeDays) : 'N/A'
      ])
    );
    
    console.log(table);
  });

program
  .command('territory-winners')
  .description('Get territory release winners')
  .action(async () => {
    const client = new Earth2Client({ cookieJar: process.env.E2_COOKIE, csrfToken: process.env.E2_CSRF });
    const res = await client.getTerritoryReleaseWinners();
    console.log(JSON.stringify(res, null, 2));
  });

program
  .command('property')
  .description('Get single property by id')
  .argument('<id>')
  .action(async (id) => {
    const client = new Earth2Client({ cookieJar: process.env.E2_COOKIE, csrfToken: process.env.E2_CSRF });
    const res = await client.getProperty(id);
    console.log(JSON.stringify(res, null, 2));
  });

program
  .command('market')
  .description('Search marketplace')
  .option('-c, --country <country>')
  .option('-t, --tier <tier>')
  .option('--tile-class <tileClass>')
  .option('--tile-count <tileCount>')
  .option('-p, --page <page>', '1')
  .option('-n, --items <items>', '100')
  .option('-s, --search <search>', '')
  .option('--term <term...>', 'additional searchTerms[]')
  .option('--json', 'Output raw JSON')
  .action(async (opts) => {
    const client = new Earth2Client({ cookieJar: process.env.E2_COOKIE, csrfToken: process.env.E2_CSRF });
    const res = await client.searchMarket({
      country: opts.country,
      landfieldTier: opts.tier,
      tileClass: opts.tileClass,
      tileCount: opts.tileCount,
      page: Number(opts.page || 1),
      items: Number(opts.items || 100),
      search: opts.search,
      searchTerms: opts.term || [],
    });
    
    if (opts.json) {
      console.log(JSON.stringify(res, null, 2));
      return;
    }
    
    console.log(chalk.bold.blue('\n🏪 Marketplace Search Results\n'));
    logInfo(`Found ${formatNumber(res.count)} total properties`);
    
    if (res.items.length === 0) {
      logInfo('No properties match your search criteria');
      return;
    }
    
    const table = formatTable(
      ['Description', 'Location', 'Country', 'Tier', 'Tiles', 'Total Price', 'Price/Tile'],
      res.items.slice(0, 20).map(item => [
        (item.description || 'N/A').substring(0, 30) + (item.description && item.description.length > 30 ? '...' : ''),
        (item.location || 'N/A').substring(0, 25) + (item.location && item.location.length > 25 ? '...' : ''),
        item.country || 'N/A',
        item.tier ? `T${item.tier}` : 'N/A',
        item.tileCount ? formatNumber(item.tileCount) : 'N/A',
        item.price ? formatPrice(item.price) : 'N/A',
        item.ppt ? formatPrice(item.ppt) : 'N/A'
      ])
    );
    
    console.log(table);
    
    if (res.items.length > 20) {
      logInfo(`Showing first 20 of ${res.items.length} results. Use --json to see all.`);
    }
  });

program
  .command('market-floor')
  .description('Compute minimal price-per-tile for given filters')
  .option('-c, --country <country>')
  .option('-t, --tier <tier>')
  .option('--tile-class <tileClass>')
  .option('--tile-count <tileCount>')
  .action(async (opts) => {
    const client = new Earth2Client({ cookieJar: process.env.E2_COOKIE, csrfToken: process.env.E2_CSRF });
    const res = await client.getMarketFloor({
      country: opts.country,
      landfieldTier: opts.tier,
      tileCount: opts.tileCount,
      tileClass: opts.tileClass,
    });
    console.log(JSON.stringify(res, null, 2));
  });

program
  .command('leaderboard')
  .description('Fetch leaderboard data')
  .option('--type <type>', 'players', 'players|countries|player_countries')
  .option('--sort_by <sortBy>', 'tiles_count')
  .option('--country <country>')
  .option('--continent <continent>')
  .action(async (opts) => {
    const client = new Earth2Client({ cookieJar: process.env.E2_COOKIE, csrfToken: process.env.E2_CSRF });
    let res: any;
    if (opts.type === 'countries') res = await client.getLeaderboardCountries(opts);
    else if (opts.type === 'player_countries') res = await client.getLeaderboardPlayerCountries(opts);
    else res = await client.getLeaderboardPlayers(opts);
    console.log(JSON.stringify(res, null, 2));
  });

program
  .command('resources')
  .description('Get resources for a property')
  .argument('<id>')
  .action(async (id) => {
    const client = new Earth2Client({ cookieJar: process.env.E2_COOKIE, csrfToken: process.env.E2_CSRF });
    try {
      const res = await client.getResources(id);
      console.log(JSON.stringify(res, null, 2));
    } catch (err: any) {
      const msg = String(err?.message || err);
      if (/\b401\b/.test(msg)) {
        logError('401 Unauthorized from resources API. This endpoint typically requires a verified (KYC) Earth2 account and an authenticated session. Please verify your account and log in, then try again.');
      } else {
        logError(`Resources request failed: ${msg}`);
      }
      process.exit(1);
    }
  });

program
  .command('avatar-sales')
  .description('Get recent avatar skin sales')
  .action(async () => {
    const client = new Earth2Client({ cookieJar: process.env.E2_COOKIE, csrfToken: process.env.E2_CSRF });
    const res = await client.getAvatarSales();
    console.log(JSON.stringify(res, null, 2));
  });

program
  .command('user')
  .description('Get public user info')
  .argument('<id>')
  .action(async (id) => {
    const client = new Earth2Client({ cookieJar: process.env.E2_COOKIE, csrfToken: process.env.E2_CSRF });
    const res = await client.getUserInfo(id);
    console.log(JSON.stringify(res, null, 2));
  });

program
  .command('users')
  .description('Get public user info for multiple users')
  .argument('<ids...>')
  .action(async (ids) => {
    const client = new Earth2Client({ cookieJar: process.env.E2_COOKIE, csrfToken: process.env.E2_CSRF });
    const res = await client.getUsers(ids);
    console.log(JSON.stringify(res, null, 2));
  });

program
  .command('my-favorites')
  .description('Get your favorited properties (auth required)')
  .action(async () => {
    const client = new Earth2Client({ cookieJar: process.env.E2_COOKIE, csrfToken: process.env.E2_CSRF });
    const res = await client.getMyFavorites();
    console.log(JSON.stringify(res, null, 2));
  });

program
  .command('stats')
  .description('Show rate limiting and usage statistics')
  .action(async () => {
    const client = new Earth2Client({ cookieJar: process.env.E2_COOKIE, csrfToken: process.env.E2_CSRF });
    const stats = client.getRateLimitStats();
    
    if ('rateLimiting' in stats && stats.rateLimiting === 'disabled') {
      logInfo('Rate limiting is disabled for this client');
      return;
    }
    
    console.log(chalk.bold.blue('\n📊 API Usage Statistics\n'));
    
    // Type guard to ensure we have RateLimitStats
    if ('totalRequests' in stats) {
      const table = formatTable(
        ['Metric', 'Value'],
        [
          ['Total Requests', formatNumber(stats.totalRequests || 0)],
          ['Blocked Requests', formatNumber(stats.blockedRequests || 0)],
          ['Current RPM', formatNumber(stats.currentRpm || 0)],
          ['Cache Size', formatNumber(stats.cacheSize || 0)],
          ['Efficiency', `${(stats.efficiency || 0).toFixed(1)}%`]
        ]
      );
      
      console.log(table);
      
      const errorCounts = stats.errorCounts || {};
      const hasErrors = Object.values(errorCounts).some((count: number) => count > 0);
      
      if (hasErrors) {
        console.log(chalk.bold.yellow('\n⚠️  Error Counts by Endpoint\n'));
        
        const errorTable = formatTable(
          ['Endpoint Category', 'Error Count'],
          Object.entries(errorCounts)
            .filter(([, count]) => (count as number) > 0)
            .map(([endpoint, count]) => [endpoint, formatNumber(count as number)])
        );
        
        console.log(errorTable);
      }
    }
  });

program
  .command('clear-cache')
  .description('Clear the response cache')
  .action(async () => {
    const client = new Earth2Client({ cookieJar: process.env.E2_COOKIE, csrfToken: process.env.E2_CSRF });
    client.clearCache();
    logSuccess('Response cache cleared');
  });

program
  .command('set-cache-ttl')
  .description('Set cache time-to-live in milliseconds')
  .argument('<ms>')
  .action(async (ms) => {
    const ttl = Number(ms);
    if (isNaN(ttl) || ttl < 0) {
      logError('Cache TTL must be a non-negative number');
      process.exit(1);
    }
    
    const client = new Earth2Client({ cookieJar: process.env.E2_COOKIE, csrfToken: process.env.E2_CSRF });
    client.setCacheTtl(ttl);
    logSuccess(`Cache TTL set to ${ttl} milliseconds`);
  });

program.parse(process.argv);


