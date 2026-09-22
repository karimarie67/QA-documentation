# Automate Release Notes for Boost.org Website

To automate release notes for boost.org website updates using GitHub Actions and send them to Slack and the boost.org mailing list. This solution focuses specifically on the **website-v2** and **website-v2-docs** repositories, which handle the main website and documentation updates respectively.

## Solution Overview

1. **Generate Release Notes**: Use GitHub's automated release notes feature to generate notes based on closed issues and PRs in website-v2 and website-v2-docs repositories
2. **Post to Slack**: Send generated release notes to designated Slack channel for immediate team notification
3. **Send to Mailing List**: Email release notes to boost.org mailing list for broader community notification
4. **Automate the Workflow**: Trigger on new release events in either repository using GitHub Actions

## Scope and Repositories

**Target Repositories:**
- **boostorg/website-v2**: Main website functionality, UI changes, feature updates
- **boostorg/website-v2-docs**: Documentation updates, content changes, library documentation

**Why This Scope:**
- Focused on user-facing changes that the community cares about
- Manageable scope for testing and iteration
- Clear ownership and release cycles
- Avoids complexity of coordinating across dozens of boost repositories

## Implementation Strategy

### Phase 1: Website-v2 Only (Proof of Concept)
Start with the main website repository to validate the approach:
- Set up GitHub Action in website-v2
- Test Slack integration
- Validate release note generation

### Phase 2: Add Documentation Repository
Extend to include documentation updates:
- Add workflow to website-v2-docs
- Coordinate release notes from both repositories
- Test combined messaging

### Phase 3: Mailing List Integration
Add email functionality after Slack is proven:
- Implement email automation with approval gates
- Test formatting for mailing list compatibility
- Consider digest vs. immediate notification options

## Detailed Implementation

### Step 1: Configure Release Notes Generation

Create `.github/release.yml` in both repositories to categorize issues and PRs:

```yaml
changelog:
  categories:
    - title: Website Features
      labels:
        - feature
        - enhancement
        - ui-improvement
    - title: Bug Fixes
      labels:
        - bug
        - hotfix
    - title: Documentation Updates
      labels:
        - documentation
        - content-update
    - title: Performance & Infrastructure
      labels:
        - performance
        - infrastructure
        - security
    - title: Other Changes
      labels:
        - '*'
      exclude:
        labels:
          - dependencies
          - internal
```

**Repository-Specific Customization:**
- **website-v2**: Focus on UI, features, performance
- **website-v2-docs**: Focus on documentation, content, library updates

### Step 2: Slack Integration Setup

**Prerequisites:**
- Create Slack App at https://api.slack.com/apps
- Enable Incoming Webhooks for target channel (e.g., #boost-website-releases)
- Store webhook URL as repository secret: `SLACK_WEBHOOK_URL`

### Step 3: Email Configuration

**SMTP Setup Options:**
- Use existing boost.org email infrastructure
- Alternative: SendGrid or similar service for reliability
- Store credentials as repository secrets:
  - `SMTP_SERVER`
  - `SMTP_PORT` 
  - `SMTP_USERNAME`
  - `SMTP_PASSWORD`

**Mailing List Considerations:**
- Verify boost.org mailing list accepts automated emails
- Consider using dedicated sender address (e.g., website-releases@boost.org)
- Test email formatting for plain text compatibility

### Step 4: GitHub Actions Workflow

Create `.github/workflows/publish-release-notes.yml` in both repositories:

```yaml
name: Publish Website Release Notes

on:
  release:
    types: [published]

jobs:
  publish-release-notes:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Generate Release Notes
        id: release-notes
        run: |
          # Get release details
          RELEASE_TAG="${{ github.event.release.tag_name }}"
          RELEASE_NAME="${{ github.event.release.name }}"
          RELEASE_BODY="${{ github.event.release.body }}"
          RELEASE_URL="${{ github.event.release.html_url }}"
          REPO_NAME="${{ github.repository }}"
          
          # Format for different outputs
          echo "RELEASE_TAG=$RELEASE_TAG" >> $GITHUB_ENV
          echo "RELEASE_NAME=$RELEASE_NAME" >> $GITHUB_ENV  
          echo "RELEASE_URL=$RELEASE_URL" >> $GITHUB_ENV
          echo "REPO_NAME=$REPO_NAME" >> $GITHUB_ENV
          
          # Store formatted release body
          echo "RELEASE_BODY<<EOF" >> $GITHUB_ENV
          echo "$RELEASE_BODY" >> $GITHUB_ENV
          echo "EOF" >> $GITHUB_ENV

      - name: Post to Slack
        uses: slackapi/slack-github-action@v2.0.0
        with:
          webhook: ${{ secrets.SLACK_WEBHOOK_URL }}
          webhook-type: webhook-trigger
          payload: |
            {
              "text": "🚀 New Boost.org Website Release",
              "blocks": [
                {
                  "type": "header",
                  "text": {
                    "type": "plain_text",
                    "text": "🚀 ${{ env.REPO_NAME }} Release: ${{ env.RELEASE_TAG }}"
                  }
                },
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Release:* ${{ env.RELEASE_NAME }}\n*Repository:* ${{ env.REPO_NAME }}\n*Tag:* ${{ env.RELEASE_TAG }}"
                  },
                  "accessory": {
                    "type": "button",
                    "text": {
                      "type": "plain_text",
                      "text": "View Release"
                    },
                    "url": "${{ env.RELEASE_URL }}"
                  }
                },
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn", 
                    "text": "${{ env.RELEASE_BODY }}"
                  }
                }
              ]
            }

      - name: Send Email to Mailing List
        uses: dawidd6/action-send-mail@v3
        with:
          server_address: ${{ secrets.SMTP_SERVER }}
          server_port: ${{ secrets.SMTP_PORT }}
          username: ${{ secrets.SMTP_USERNAME }}
          password: ${{ secrets.SMTP_PASSWORD }}
          subject: "Boost.org Website Update: ${{ env.RELEASE_TAG }} (${{ env.REPO_NAME }})"
          body: |
            Boost.org Website Release Notification
            =====================================
            
            Repository: ${{ env.REPO_NAME }}
            Release: ${{ env.RELEASE_NAME }}
            Tag: ${{ env.RELEASE_TAG }}
            
            Release Notes:
            --------------
            ${{ env.RELEASE_BODY }}
            
            View full release details: ${{ env.RELEASE_URL }}
            
            ---
            This is an automated notification from the Boost.org website release system.
            To modify notification preferences, contact the website team.
          to: boost@lists.boost.org
          from: "Boost Website Releases <website-releases@boost.org>"
          content_type: text/plain

      - name: Create Deployment Record
        run: |
          echo "Release ${{ env.RELEASE_TAG }} published successfully" >> deployment.log
          echo "Slack notification: Sent"
          echo "Email notification: Sent to boost@lists.boost.org"
          echo "Timestamp: $(date -u)"
```

## Repository-Specific Workflows

### Website-v2 Releases
**Typical Content:**
- New features and UI improvements
- Bug fixes and performance optimizations
- Security updates
- Infrastructure changes

**Release Frequency:** Monthly or as needed for critical updates

### Website-v2-docs Releases
**Typical Content:**
- Documentation updates and corrections
- New library documentation
- Content reorganization
- Search and navigation improvements

**Release Frequency:** Weekly or as content is updated

## Setup Instructions

### 1. Repository Configuration
For both website-v2 and website-v2-docs repositories:

**GitHub Secrets (Settings > Secrets and variables > Actions):**
- `SLACK_WEBHOOK_URL`: Slack incoming webhook URL
- `SMTP_SERVER`: Email server address
- `SMTP_PORT`: Email server port (usually 587 or 465)
- `SMTP_USERNAME`: Email authentication username
- `SMTP_PASSWORD`: Email authentication password

### 2. Slack Workspace Setup
- Create dedicated channel: #boost-website-releases
- Configure Slack app with incoming webhook
- Test webhook with sample payload

### 3. Email Configuration
- Verify boost.org mailing list accepts automated emails
- Configure sender authentication (SPF, DKIM if needed)
- Test email delivery with sample message

### 4. Testing Protocol
**Before Production:**
1. Create test release in repository
2. Verify Slack message formatting
3. Test email delivery and formatting
4. Confirm all links and references work
5. Validate with small test group

**Production Rollout:**
1. Deploy to website-v2 first
2. Monitor for 1-2 releases
3. Extend to website-v2-docs
4. Gather feedback and iterate

## Alternative: Manual Approval Gate

For additional control, add manual approval before sending emails:

```yaml
- name: Request Approval for Email
  uses: trstringer/manual-approval@v1
  with:
    secret: ${{ github.TOKEN }}
    approvers: website-team-leads
    minimum-approvals: 1
    issue-title: "Approve release notification for ${{ env.RELEASE_TAG }}"
```

## Monitoring and Maintenance

**Success Metrics:**
- Slack notifications delivered successfully
- Email delivery confirmation
- Community engagement with release notifications
- Reduced manual communication overhead

**Ongoing Maintenance:**
- Monitor email deliverability
- Update notification formatting based on feedback
- Adjust release note categorization as needed
- Review and update mailing list recipients

## Security Considerations

- Store all credentials in GitHub Secrets, never in code
- Use least-privilege access for SMTP credentials
- Regularly rotate webhook URLs and passwords
- Monitor for unauthorized access to notification systems
- Consider rate limiting for high-frequency releases

## Resources

- [GitHub Automatic Release Notes](https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes)
- [Slack GitHub Action](https://github.com/slackapi/slack-github-action)
- [Send Mail Action](https://github.com/dawidd6/action-send-mail)
- [Manual Approval Action](https://github.com/trstringer/manual-approval)
#### **Step 4: Create a GitHub Actions Workflow**

GitHub Actions Workflow for Release Notes  

```name: Publish Release Notes

on:
  release:
    types: [published]

jobs:
  generate-and-publish-release-notes:
    runs-on: ubuntu-latest
    steps:
      # Checkout the repository
      - name: Checkout
        uses: actions/checkout@v4

      # Generate release notes using GitHub API
      - name: Generate Release Notes
        id: release-notes
        run: |
          RELEASE_NOTES=$(gh release view ${{ github.event.release.tag_name }} --json body --jq '.body')
          echo "RELEASE_NOTES<<EOF" >> $GITHUB_ENV
          echo "$RELEASE_NOTES" >> $GITHUB_ENV
          echo "EOF" >> $GITHUB_ENV
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      # Post to Slack
      - name: Send to Slack
        uses: slackapi/slack-github-action@v2.0.0
        with:
          webhook: ${{ secrets.SLACK_WEBHOOK_URL }}
          webhook-type: webhook-trigger
          payload: |
            {
              "text": "New Release: ${{ github.event.release.tag_name }}\n\n${{ env.RELEASE_NOTES }}"
            }

      # Send email to mailing list
      - name: Send Email
        uses: dawidd6/action-send-mail@v3
        with:
          server_address: ${{ secrets.SMTP_SERVER }}
          server_port: ${{ secrets.SMTP_PORT }}
          username: ${{ secrets.SMTP_USERNAME }}
          password: ${{ secrets.SMTP_PASSWORD }}
          subject: "Boost.org Release Notes: ${{ github.event.release.tag_name }}"
          body: |
            New Release: ${{ github.event.release.tag_name }}

            ${{ env.RELEASE_NOTES }}

            View the release on GitHub: ${{ github.event.release.html_url }}
          to: boost@lists.boost.org
          from: "Boost.org Releases <no-reply@boost.org>"
```

#### **How It Works**

* **Trigger**: The workflow runs when a new release is published (e.g., when you create a release in GitHub with a tag).  
* **Generate Release Notes**: The gh release view command retrieves the release notes generated by GitHub, stored in the RELEASE\_NOTES environment variable.  
* **Slack Notification**: The slackapi/slack-github-action sends the release notes to the specified Slack channel using the webhook.  
* **Email Notification**: The dawidd6/action-send-mail action sends an email to boost@lists.boost.org with the release notes and a link to the GitHub release.

#### **Setup Instructions**

1. **Enable GitHub Actions**: Ensure GitHub Actions is enabled in the proper repository.  
2. **Configure Secrets**:  
   * In the GitHub repository, go to Settings \> Secrets and variables \> Actions.  
   * Add SLACK\_WEBHOOK\_URL (from Slack).  
   * Add SMTP\_SERVER, SMTP\_PORT, SMTP\_USERNAME, SMTP\_PASSWORD (from our email provider).  
3. **Add Workflow File**: Place the above YAML in .github/workflows/publish-release-notes.yml.  
4. **Label Issues**: Ensure issues in GitHub Projects are labeled appropriately (e.g., "feature," "bug") to match the release.yml configuration.  
5. **Test the Workflow**: Create a test release in GitHub to verify that the notes are generated, posted to Slack, and emailed to the mailing list.

#### **Alternative: Custom Script for Release Notes**

If GitHub’s automated release notes don’t meet our needs, we can use a Python script to query the GitHub API for closed issues and format them. Here’s an example script:

Generate Release Notes Script  

```python import requests
import requests
import os

def generate_release_notes(repo, token, project_id):
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    # Get issues from a specific project
    query = f"https://api.github.com/repos/{repo}/issues?state=closed&labels=release"
    response = requests.get(query, headers=headers)
    issues = response.json()

    notes = f"# Release Notes for {repo}\n\n"
    for issue in issues:
        notes += f"- {issue['title']} (#{issue['number']})\n"
    return notes

if __name__ == "__main__":
    repo = "boostorg/boost"  # Replace with proper repo if incorrect
    token = os.getenv("GITHUB_TOKEN")
    project_id = "our-project-id"  # Replace with GitHub Project ID
    release_notes = generate_release_notes(repo, token, project_id)
    print(release_notes)
```

* **Run the Script**: Add this script to the GitHub Actions workflow, replacing the gh release view step, and store the output in RELEASE\_NOTES.  
* **Dependencies**: Install requests in the workflow using pip install requests.

#### **Additional Considerations**

* **Formatting for Mailing List**: Ensure the release notes are plain text or lightly formatted (e.g., Markdown) for email compatibility. Test the email output to ensure readability.  
* **Rate Limits**: Be mindful of rate limits when querying issues. Use pagination if dealing with many issues.  
* **Slack Customization**: Use Slack’s block kit for richer message formatting if desired.  
* **Security**: Keep SMTP credentials and Slack webhook URLs secure in GitHub Secrets.  
* **Testing**: Test the workflow with a draft release to avoid spamming the mailing list or Slack channel.

#### **Resources**

* GitHub Automatic Release Notes: [https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes\[](https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes%5B)\]([https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes](https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes))  
* Slack GitHub Action: [https://github.com/slackapi/slack-github-action\[](https://github.com/slackapi/slack-github-action%5B)\]([https://github.com/slackapi/slack-github-action](https://github.com/slackapi/slack-github-action))  
* Send Mail Action: [https://github.com/dawidd6/action-send-mail](https://github.com/dawidd6/action-send-mail)  
* Boost.org Mailing List: Ensure the mailing list accepts automated emails or configure an approved sender.
