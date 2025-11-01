# Remove the git lock file
rm /home/runner/workspace/.git/index.lock

# Stage all changes
cd /home/runner/workspace
git add app/config/settings.py
git add app/handlers/request_handler.py
git add app/utils/conversational_prompts.py
git add app/utils/dividend_analytics.py
git add deploy/AZURE_RUN_COMMAND_DEPLOY.sh
git add deploy/DEPLOYMENT_INSTRUCTIONS.md
git add DEPLOYMENT_UPDATE_SUMMARY.md

# Commit with descriptive message
git commit -m "Add dividend alert suggestions + fix Azure deployment script

Features:
- Proactive dividend declaration alert suggestions (medium/high confidence only)
- Frequency detection and next ex-date prediction
- Confidence-based gating per architect review

Deployment Fix:
- Updated AZURE_RUN_COMMAND_DEPLOY.sh to clone full repo from GitHub
- Updated deployment instructions with clear steps
- Added DEPLOYMENT_UPDATE_SUMMARY.md documentation"

# Push to GitHub
git push origin main

