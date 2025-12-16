import { amber } from "@mui/material/colors";

//Display time interval (since last scrape / until next scrape / overdue since) in two highest divisible units
function formatTimeInterval(ms) {
  let result = "";
  let matched = 0;
  const units = {
    days: 86400000,
    hours: 3600000,
    minutes: 60000,
    seconds: 1000,
  };
  for (const [unit, value] of Object.entries(units)) {
    if (ms >= value && matched < 2) {
      matched += 1;
      const count = Math.floor(ms / value);
      result += `${count}${unit.charAt(0)} `;
      ms -= count * value;
    }
  }
  return result || "now";
}

//Get status info for the source (due / overdue / never scraped / currently scraping / failed)
export function getScrapingSourceStatus(source) {
  const now = new Date();
  const scrapingFrequencyMs = source.scraping_frequency * 60 * 1000;
  let lastScrapedDate = source.last_scraped_at
    ? new Date(source.last_scraped_at)
    : null;
  if (lastScrapedDate && lastScrapedDate.getFullYear() <= 1900) {
    lastScrapedDate = null;
  }

  const lastScrapedFormatted = lastScrapedDate
    ? formatTimeInterval(now - lastScrapedDate)
    : null;

  let statusDot = "";
  let statusText = "";
  let statusColor = "";
  let state = "";

  if (source.currently_scraping) {
    state = "scraping";
    statusDot = "🟡";
    statusText = `Currently scraping • Last scraped: ${
      lastScrapedFormatted ? `${lastScrapedFormatted} ago` : "never"
    }`;
    statusColor = amber[700];
  } else if (lastScrapedDate) {
    const nextDueDate = new Date(
      lastScrapedDate.getTime() + scrapingFrequencyMs
    );
    const timeUntilNextDue = nextDueDate - now;
    const nextDueFormatted =
      timeUntilNextDue > 0
        ? `Due in ${formatTimeInterval(timeUntilNextDue)}`
        : `Overdue by ${formatTimeInterval(Math.abs(timeUntilNextDue))}`;

    if (source.last_error) {
      state = "failed";
      statusDot = "❌";
      statusText = `Failed: ${source.last_error}\n\n • Last success: ${
        lastScrapedFormatted ? `${lastScrapedFormatted} ago` : "never"
      } • ${nextDueFormatted}`;
      statusColor = "error.main";
    } else if (timeUntilNextDue > 0) {
      state = "scheduled";
      statusDot = "🟢";
      statusText = `Last scraped: ${lastScrapedFormatted} ago • ${nextDueFormatted}`;
      statusColor = "success.main";
    } else {
      state = "overdue";
      statusDot = "🔴";
      statusText = `Last scraped: ${lastScrapedFormatted} ago • ${nextDueFormatted}`;
      statusColor = "error.main";
    }
  } else {
    state = "never_scraped";
    statusDot = "⚪";
    statusText = "Never scraped";
    statusColor = "text.disabled";
  }

  return {
    statusDot,
    statusText,
    statusColor,
    state,
  };
}
