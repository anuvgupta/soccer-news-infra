import chromium from '@sparticuz/chromium';
import puppeteer from 'puppeteer-core';

/**
 * Lambda handler for headless browsing with Puppeteer
 * 
 * Event format:
 * {
 *   url: string (required) - The URL to fetch
 *   waitUntil?: 'load' | 'domcontentloaded' | 'networkidle0' | 'networkidle2' (default: 'networkidle0')
 *   timeout?: number (default: 60000) - Navigation timeout in milliseconds
 *   waitForSelector?: string - Optional CSS selector to wait for before returning
 *   delay?: number - Additional delay in milliseconds after page load
 * }
 * 
 * Response format:
 * {
 *   statusCode: 200,
 *   body: {
 *     html: string - Full HTML content after JavaScript rendering
 *     url: string - Final URL (after any redirects)
 *     timestamp: string - ISO timestamp of the capture
 *   }
 * }
 */
export const handler = async (event, context) => {
    console.log('Event received:', JSON.stringify(event, null, 2));
    
    let browser = null;
    
    try {
        // Validate input
        if (!event.url) {
            return {
                statusCode: 400,
                body: JSON.stringify({
                    error: 'Missing required parameter: url'
                })
            };
        }
        
        const url = event.url;
        const waitUntil = event.waitUntil || 'networkidle0';
        const timeout = event.timeout || 60000;
        const waitForSelector = event.waitForSelector;
        const delay = event.delay || 2000;
        
        console.log(`Launching browser for URL: ${url}`);
        console.log(`Configuration: waitUntil=${waitUntil}, timeout=${timeout}, delay=${delay}`);
        
        // Launch browser with optimized settings for Lambda
        browser = await puppeteer.launch({
            args: chromium.args,
            defaultViewport: chromium.defaultViewport,
            executablePath: await chromium.executablePath(),
            headless: chromium.headless,
            ignoreHTTPSErrors: true,
        });
        
        console.log('Browser launched successfully');
        
        // Create a new page
        const page = await browser.newPage();
        
        // Set user agent to avoid bot detection
        await page.setUserAgent(
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        );
        
        // Set extra HTTP headers
        await page.setExtraHTTPHeaders({
            'Accept-Language': 'en-US,en;q=0.9'
        });
        
        console.log(`Navigating to ${url}...`);
        
        // Navigate to the URL
        await page.goto(url, {
            waitUntil: waitUntil,
            timeout: timeout
        });
        
        console.log('Page loaded, waiting for content to render...');
        
        // If a specific selector is requested, wait for it
        if (waitForSelector) {
            console.log(`Waiting for selector: ${waitForSelector}`);
            await page.waitForSelector(waitForSelector, { timeout: 10000 });
        }
        
        // Additional delay to ensure JavaScript has fully rendered
        if (delay > 0) {
            console.log(`Waiting additional ${delay}ms for JavaScript rendering...`);
            await new Promise(resolve => setTimeout(resolve, delay));
        }
        
        // Get the final URL (after any redirects)
        const finalUrl = page.url();
        
        // Get the full HTML content
        const html = await page.content();
        
        console.log(`Successfully captured HTML from ${finalUrl}`);
        console.log(`HTML length: ${html.length} characters`);
        
        // Close the browser
        await browser.close();
        browser = null;
        
        return {
            statusCode: 200,
            body: {
                html: html,
                url: finalUrl,
                timestamp: new Date().toISOString()
            }
        };
        
    } catch (error) {
        console.error('Error during browser operation:', error);
        
        // Make sure to close browser on error
        if (browser) {
            try {
                await browser.close();
            } catch (closeError) {
                console.error('Error closing browser:', closeError);
            }
        }
        
        return {
            statusCode: 500,
            body: {
                error: error.message,
                stack: error.stack,
                url: event.url
            }
        };
    }
};

