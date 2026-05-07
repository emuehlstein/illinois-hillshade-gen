## Hillshade Generation Request

**County:** <!-- e.g., Will, Kane, etc. -->

**DEM Type:** <!-- DTM (bare earth) or DSM (surface model) -->

**Styles:** <!-- dark, light, tactical, terrain, gray -->

**Exaggerations:** <!-- e.g., 9 (recommended for IL) -->

**Zoom Range:** <!-- optional, default: 10-16 -->

### Checklist

- [ ] I've added my request to `requests.yaml`
- [ ] I've checked that this county isn't already generated
- [ ] I understand this will launch an AWS EC2 instance (~$0.50 cost)
- [ ] I'll actually use these tiles (not just testing)

### Use Case

<!-- Optional: What will you use these tiles for? (ATAK, web map, GIS, etc.) -->

---

**Note:** After merge, GitHub Actions will generate your tiles automatically. You'll get a comment with a preview link when ready (usually 30-60 minutes).
