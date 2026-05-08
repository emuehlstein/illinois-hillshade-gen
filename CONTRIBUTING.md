# Contributing to Illinois Hillshade Generator

Thank you for your interest! We welcome community contributions for new county/region hillshades.

## Request a New Hillshade

**The easy way** — open a PR:

1. Fork this repo
2. Edit `requests.yaml` and add your county at the bottom:
   ```yaml
   - county: YOUR_COUNTY_NAME
     dem: dtm              # or dsm
     styles:
       - dark              # dark, light, tactical, terrain, gray
     exaggerations:
       - 9                 # 1-30, higher = more dramatic
     zoom: "10-16"         # optional, default 10-16
   ```
3. Open a pull request
4. Our CI/CD pipeline will generate the tiles on merge
5. You'll get a comment with a preview link when ready!

## What Happens

When your PR is merged:
- GitHub Actions launches an EC2 spot instance
- Generates hillshade tiles (~30-60 min for most counties)
- Uploads to S3 and our tile server
- Updates `requests.yaml` with status + preview link
- Comments on your PR with the live URL

## Supported Counties

Currently: **Illinois counties** via [ISGS elevation data](https://clearinghouse.isgs.illinois.edu/data/elevation)

Support for nationwide USGS 3DEP and custom DEMs coming soon!

## Styles

- **dark** — Blue-grey, ATAK dark mode (default)
- **light** — Warm beige, web/light mode
- **tactical** — Green-grey, military maps
- **terrain** — Brown-green, topographic
- **gray** — Pure grayscale

## Exaggeration

- **3x** — Subtle, realistic terrain
- **9x** — Balanced (recommended for flat IL terrain)
- **15x** — Dramatic, good for LiDAR micro-relief

You can request multiple styles/exaggerations in one PR — they'll all be generated.

## Examples

**Simple request:**
```yaml
- county: will
  dem: dtm
  styles: [dark]
  exaggerations: [9]
```

**Multi-style request:**
```yaml
- county: kane
  dem: dtm
  styles: [dark, light, tactical]
  exaggerations: [3, 9, 15]
  # This generates 9 mbtiles (3 styles × 3 exaggerations)
```

## Cost

Generation is free! We run on AWS spot instances (~$0.50/county).

Please be respectful:
- Don't request duplicates
- Check `requests.yaml` first to see what exists
- Limit requests to counties you'll actually use

## Questions?

Open an issue or ask in [Discussions](https://github.com/emuehlstein/illinois-hillshade-gen/discussions)!
