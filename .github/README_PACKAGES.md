# 📦 Making Docker Images Public

After GitHub Actions builds your images, you need to make them public so your NAS can pull them without authentication.

## Steps to Make Images Public

### 1. Go to Your Packages
Visit: https://github.com/jitension?tab=packages

### 2. Make Backend Image Public
1. Click on **`portfolio-backend`**
2. Click **"Package settings"** (on the right side)
3. Scroll to bottom → **"Danger Zone"**
4. Click **"Change visibility"**
5. Select **"Public"**
6. Type the repository name to confirm
7. Click **"I understand, change package visibility"**

### 3. Make Frontend Image Public
1. Go back to packages: https://github.com/jitension?tab=packages
2. Click on **`portfolio-frontend`**
3. Repeat steps 2-7 above

## Why Make Them Public?

**Option 1: Public Images (Recommended for personal NAS)**
- ✅ NAS can pull without authentication
- ✅ Simpler deployment
- ✅ Faster pulls (no login needed)
- ⚠️ Anyone can pull your images (but they can't access your app without credentials)

**Option 2: Keep Private**
- ✅ More secure (only authenticated users can pull)
- ⚠️ Need to login to GHCR on NAS
- ⚠️ Need to manage authentication tokens on NAS

## If Keeping Private

To pull private images on your NAS:

```bash
# On NAS, login to GHCR first
echo "YOUR_GITHUB_TOKEN" | docker login ghcr.io -u jitension --password-stdin

# Then pull normally
docker-compose -f docker-compose.nas.yml pull
```

## Security Note

Your Docker images contain your **compiled code**, but NOT your:
- ❌ Environment variables (.env file)
- ❌ Database passwords
- ❌ API keys
- ❌ User data

So making images public is generally safe for personal projects. The sensitive data is in your `.env` file on the NAS, which is never in the image.

## Verifying Images Are Public

After making them public, try pulling without authentication:

```bash
# Should work without docker login
docker pull ghcr.io/jitension/portfolio-backend:latest
docker pull ghcr.io/jitension/portfolio-frontend:latest
```

If you see "Error: unauthorized", the images are still private.
