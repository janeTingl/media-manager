# Analytics Dashboard User Guide

## Quick Start

1. **Open Media Manager** - Launch the application
2. **Click the "Dashboard" Tab** - Located in the main window's tab bar
3. **View Your Statistics** - See summary cards and activity feed

## Features Overview

### Summary Cards

The dashboard displays five key statistics:

- **Total Items** - Total number of movies and TV shows
- **Movies** - Number of movies in your library
- **TV Shows** - Number of TV series
- **Total Runtime** - Combined runtime of all media (in hours)
- **Storage** - Total disk space used by all media (in GB)

### Filter Controls

#### Library Selection
- **Dropdown Menu**: Select a specific library or "All Libraries"
- **Effect**: Updates all statistics to show data only from selected library
- **Default**: Shows all libraries

#### Date Range
- **From Date**: Set the start date for activity filtering
- **To Date**: Set the end date for activity filtering
- **Effect**: Filters recent activity to show events in the specified range
- **Default**: Last 30 days

#### Refresh Button
- **Manual Refresh**: Click to immediately refresh all statistics
- **Auto-Refresh**: Optional background refresh (not auto-enabled)

### Top Lists

#### Top Directors
- Shows directors with the most items in your library
- Displays count of items for each director
- Updates based on selected library
- Useful for discovering prolific directors

#### Top Actors
- Shows actors with the most items in your library
- Displays count of items for each actor
- Updates based on selected library
- Useful for discovering frequently featured actors

### Recent Activity

Shows recent events from your media library:

- **Added Events**: When new media was added to library
- **Modified Events**: When media metadata was modified
- **Watched Events**: When media was marked as watched
- **Timestamp**: Shows when each event occurred
- **Media Title**: Shows which item the event is for

Events are displayed in reverse chronological order (most recent first).

## Interpretation Guide

### Completion Statistics

The dashboard shows metadata completion percentages:

- **Description Completion**: % of items with descriptions
- **Rating Completion**: % of items with ratings
- **Runtime Completion**: % of items with runtime

Higher percentages indicate more complete metadata.

### Storage Insights

- **Total Storage**: Sum of all media file sizes
- **Per-Item Average**: Total storage ÷ number of items
- **By Type**: Compare storage between movies and TV

### Activity Insights

- **Recent Adds**: Shows when library is actively growing
- **Modifications**: Indicates ongoing metadata editing
- **Watched Events**: Shows which media is being watched

## Common Tasks

### Find Your Most Prolific Director
1. Go to Dashboard tab
2. Look at "Top Directors" section
3. Director at top has most items

### Check Library Storage Usage
1. Go to Dashboard tab
2. Look at "Storage" card
3. Shows total storage in GB

### See Recent Changes
1. Go to Dashboard tab
2. Scroll to "Recent Activity" section
3. Review timestamps and event types

### Filter by Specific Library
1. Go to Dashboard tab
2. Click library dropdown
3. Select desired library
4. All statistics update automatically

### Track Metadata Completion
1. Go to Dashboard tab
2. Look at completion percentages
3. Higher = more complete metadata

## Performance Notes

- **Initial Load**: First dashboard view may take 1-2 seconds
- **Cached Data**: Subsequent views are very fast (<100ms)
- **Cache Duration**: Statistics cached for 5 minutes
- **Manual Refresh**: Click "Refresh" to get latest data immediately

## Tips & Tricks

### Organization
- Use different libraries for different media types
- Keep related media in same library
- Color-code libraries for visual identification

### Metadata Quality
- Monitor completion percentages regularly
- Aim for >90% description completion
- Complete ratings before archiving media

### Activity Tracking
- Watch recent activity to see library changes
- Use date range to analyze activity periods
- Track when items were added vs. modified

### Discovery
- Use top lists to find prolific directors/actors
- Compare top lists across libraries
- Identify gaps in director/actor coverage

## Troubleshooting

### Dashboard Shows Zero Items
- **Cause**: Library is empty or no library selected
- **Solution**: Add media to library or select a library with items

### Statistics Are Outdated
- **Cause**: Showing cached data
- **Solution**: Click "Refresh" button to fetch fresh data

### Storage Size Seems Wrong
- **Cause**: Recently deleted files still in cache
- **Solution**: Click "Refresh" to clear cache and recalculate

### Activity Feed Is Empty
- **Cause**: No recent events or filtered by wrong date range
- **Solution**: Adjust date range or add new media to generate events

### Dashboard Is Slow
- **Cause**: Very large media library
- **Solution**: Filter by specific library to reduce data scope

## Keyboard Shortcuts

- **No dedicated shortcuts** for dashboard
- Use standard navigation to open Dashboard tab
- Tab navigation works normally

## Data Privacy

- All statistics are calculated locally
- No data is sent to external servers
- Statistics based on your database only
- Activity data stored in your database

## Advanced Usage

### Developer/Power User Access

To access raw statistics programmatically:

```python
from src.media_manager.stats_service import StatsService

stats = StatsService()
counts = stats.get_item_counts()
print(f"Total items: {counts['total']}")
```

See `ANALYTICS_DASHBOARD_IMPLEMENTATION.md` for full API documentation.

## Support

For issues or feature requests:
1. Check this guide for troubleshooting
2. Review the implementation documentation
3. Contact development team with specific details
