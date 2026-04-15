# PHP UI Alignment Execution

## Files updated
- `php/index.php`
- `php/health.php`
- `php/inc/layout.php`

## Branding changes
- Updated both PHP pages to use the visible main heading `My Data Lake`.
- Added a small secondary label under the heading: `Services` on the index page and `Health` on the health page.
- Aligned page title metadata defaults and per-page titles to `My Data Lake`.

## Menu alignment changes
- Updated the local hard-coded menu to match the public Hugo menu labels and ordering as closely as practical: `Home`, `Products`, `My Data Lake`, `Services`, `Insights`, `Contact`.
- Kept local usability by mapping `Services` to `/index.php` and adding a local `Health` entry at `/health.php`.
- Preserved public-site URLs for shared top-level navigation items where they have a meaningful public destination.

## Notes
- The public Hugo source of truth was read from `/Users/marekczarnecki/Documents/GitHub/oss-data-lake-landing/config.toml`.
- `Services` uses the local PHP services page instead of the public `/services/` URL so the local service launcher remains directly accessible.
- `Health` is retained as a local-only navigation item because it supports the local PHP service pages and has no matching public menu item in the Hugo config.
