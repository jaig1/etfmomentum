/**
 * UI Screen Integration Test
 * Tests the actual React UI screens using Playwright
 */

import { chromium } from 'playwright';
import fs from 'fs';

async function testDashboardScreen(page) {
    console.log('\n' + '='.repeat(70));
    console.log('TEST 1: DASHBOARD SCREEN');
    console.log('='.repeat(70));

    try {
        await page.goto('http://localhost:3000/', { waitUntil: 'networkidle', timeout: 15000 });

        // Wait for loading spinner to disappear
        await page.waitForSelector('.loading-container', { state: 'hidden', timeout: 20000 }).catch(() => {});

        // Wait for dashboard content to load
        await page.waitForSelector('.card', { timeout: 20000 });
        await page.waitForSelector('.card-title', { timeout: 5000 });

        // Take screenshot
        await page.screenshot({ path: 'screenshots/dashboard.png', fullPage: true });

        console.log('\n✅ DASHBOARD SCREEN TEST PASSED - Page loaded and data displayed');
        return true;
    } catch (error) {
        console.log(`\n❌ DASHBOARD SCREEN TEST FAILED: ${error.message}`);
        await page.screenshot({ path: 'screenshots/dashboard-error.png', fullPage: true });
        return false;
    }
}

async function testSignalsScreen(page) {
    console.log('\n' + '='.repeat(70));
    console.log('TEST 2: SIGNALS SCREEN');
    console.log('='.repeat(70));

    try {
        // Navigate to Signals page
        await page.click('text=Signals');
        await page.waitForTimeout(1000);

        // Click Generate Signals button
        await page.click('button:has-text("Generate Signals")');
        console.log('  Clicked Generate Signals button');

        // Wait for loading to complete
        await page.waitForTimeout(3000);

        // Take screenshot
        await page.screenshot({ path: 'screenshots/signals.png', fullPage: true });

        console.log('\n✅ SIGNALS SCREEN TEST PASSED - Page loaded and button clicked');
        return true;
    } catch (error) {
        console.log(`\n❌ SIGNALS SCREEN TEST FAILED: ${error.message}`);
        await page.screenshot({ path: 'screenshots/signals-error.png', fullPage: true });
        return false;
    }
}

async function testBacktestScreen(page) {
    console.log('\n' + '='.repeat(70));
    console.log('TEST 3: BACKTEST SCREEN');
    console.log('='.repeat(70));

    try {
        // Navigate to Backtest page
        await page.click('text=Backtest');
        await page.waitForTimeout(1000);

        // Fill in form
        const startDateInput = await page.$('input[type="date"]');
        if (startDateInput) {
            await startDateInput.fill('2026-01-01');
            console.log('  Filled start date');
        }

        // Click Run Backtest button
        await page.click('button:has-text("Run Backtest")');
        console.log('  Clicked Run Backtest button');

        // Wait for processing
        await page.waitForTimeout(10000);

        // Take screenshot
        await page.screenshot({ path: 'screenshots/backtest.png', fullPage: true });

        console.log('\n✅ BACKTEST SCREEN TEST PASSED - Page loaded and form submitted');
        return true;
    } catch (error) {
        console.log(`\n❌ BACKTEST SCREEN TEST FAILED: ${error.message}`);
        await page.screenshot({ path: 'screenshots/backtest-error.png', fullPage: true });
        return false;
    }
}

async function main() {
    console.log('='.repeat(70));
    console.log('ETF MOMENTUM STRATEGY - UI SCREEN TEST');
    console.log('='.repeat(70));
    console.log('Testing UI at: http://localhost:3000');

    // Create screenshots directory
    if (!fs.existsSync('screenshots')) {
        fs.mkdirSync('screenshots');
    }

    // Launch browser
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
        viewport: { width: 1280, height: 720 }
    });
    const page = await context.newPage();

    // Run tests
    const results = [];
    results.push({ name: 'Dashboard Screen', passed: await testDashboardScreen(page) });
    results.push({ name: 'Signals Screen', passed: await testSignalsScreen(page) });
    results.push({ name: 'Backtest Screen', passed: await testBacktestScreen(page) });

    // Close browser
    await browser.close();

    // Print summary
    console.log('\n' + '='.repeat(70));
    console.log('TEST SUMMARY');
    console.log('='.repeat(70));

    for (const result of results) {
        const status = result.passed ? '✅ PASSED' : '❌ FAILED';
        console.log(`${result.name.padEnd(30)} ${status}`);
    }

    const allPassed = results.every(r => r.passed);

    console.log('='.repeat(70));
    if (allPassed) {
        console.log('🎉 ALL UI TESTS PASSED!');
        console.log('\nScreenshots saved to ui/screenshots/ directory');
    } else {
        console.log('⚠️  SOME UI TESTS FAILED - Review screenshots in ui/screenshots/ directory');
    }
    console.log('='.repeat(70));

    process.exit(allPassed ? 0 : 1);
}

main().catch(error => {
    console.error('Test execution failed:', error);
    process.exit(1);
});
