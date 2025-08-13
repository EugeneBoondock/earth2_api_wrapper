#!/usr/bin/env node
import { Command } from 'commander';
import { Earth2Client } from './lib/client';

const program = new Command();
program
  .name('e2')
  .description('Earth2 API CLI (unofficial)')
  .version('0.1.0');

program
  .command('trending')
  .description('Get trending places')
  .action(async () => {
    const client = new Earth2Client({ cookieJar: process.env.E2_COOKIE, csrfToken: process.env.E2_CSRF });
    const res = await client.getTrendingPlaces();
    console.log(JSON.stringify(res, null, 2));
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
    console.log(JSON.stringify(res, null, 2));
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
    const res = await client.getResources(id);
    console.log(JSON.stringify(res, null, 2));
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

program.parse(process.argv);


