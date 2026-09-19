# PlainRead

Explains rental agreements in plain language, in the reader's own language —
built for the WeMakeDevs × AWS Bharat Builds Tour (First Commit, Sept 17–20).

**Stack:** Amazon Bedrock (foundation model) · AWS Lambda · Amazon API Gateway ·
AWS Amplify Hosting (for the frontend)

---

## Why this idea

My pick: the **Document Explainer Agent** (idea #1 from the prompt list) —
folding in idea #4 (local-language interface) as a bonus feature, not a
separate project. Reasons this beats the other options for a solo, 4-day
build:

- **It's genuinely useful and relatable.** Everyone in India has stared at a
  confusing electricity bill, rental agreement, or syllabus. Judges will
  "get it" in 10 seconds, which matters a lot in a 3-minute demo.
- **AWS sits at the actual core, not just the README.** This is built on
  Bedrock (foundation models) for the explaining itself — exactly the
  "Built on AWS — where you win or lose" judging criterion.
- **It's solo-buildable in 4 days.** The scope is naturally small: upload a
  document → extract text → explain it in plain language. One clean
  pipeline, not a sprawling app.
- **The local-language angle is a natural upgrade, not extra work.** Once
  the explainer works in English, adding "explain in Hindi/Bengali/Tamil"
  is just a prompt change to Bedrock, not new infrastructure — and it's a
  strong differentiator for Best UI and Best Blog.

**Status: idea #4 is implemented, not just planned.** The language dropdown
in `frontend/index.html` sends a `language` field to the API, and
`backend/app.py`'s Bedrock prompt generates the explanation natively in that
language (Hindi, Bengali, Tamil, Telugu, Marathi, Kannada, or English) rather
than translating an English draft afterward. See the comments marked
`Idea #4` in both files.

---

## What's in this repo

```
rental-agreement-explainer/
├── frontend/
│   └── index.html        # single-page app, no build step needed
├── backend/
│   ├── app.py             # Lambda handler that calls Bedrock
│   └── requirements.txt
├── template.yaml           # SAM template: Lambda + API Gateway
└── README.md
```

## 1. One-time AWS setup

1. **Enable a Bedrock model** in your account: AWS Console → Amazon Bedrock →
   Model access → request access to an Anthropic Claude model (e.g. Claude
   3.5 Sonnet). This is usually instant approval.
2. Note which **region** you enabled it in (e.g. `ap-south-1` for Mumbai, or
   `us-east-1` if Claude isn't yet available in your closest region — check
   Bedrock's region availability page).
3. Install the [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
   and configure AWS credentials (`aws configure`) using the free credits
   from your Builder Center account.

## 2. Deploy the backend

```bash
cd rental-agreement-explainer
sam build
sam deploy --guided
```

During `--guided`, set:
- Stack name: `plainread`
- AWS Region: the region where you enabled Bedrock access
- Parameter `BedrockRegion`: same region
- Parameter `BedrockModelId`: the model ID you were granted access to
- Allow SAM to create IAM roles: **yes**

When it finishes, copy the `ApiUrl` value from the Outputs — that's your
API Gateway endpoint.

## 3. Wire up the frontend

Open `frontend/index.html`, find this line near the bottom:

```js
const API_ENDPOINT = "PASTE_YOUR_API_GATEWAY_URL_HERE";
```

Replace it with the `ApiUrl` output from step 2.

## 4. Host it on Amplify (Ship It track)

Easiest path for a solo hackathon build:

1. Push this repo to a GitHub repo (public, since Best Blog / judging likes
   to see the code).
2. AWS Console → **AWS Amplify** → **New app** → **Host web app** → connect
   the GitHub repo.
3. Since `frontend/index.html` needs no build step, set the build output
   directory to `frontend` (or just deploy the `frontend/` folder as a
   static site — Amplify's "manual deploy" drag-and-drop also works for a
   single HTML file if you're short on time).
4. Amplify gives you a live URL in a few minutes — that's what you submit.

## 5. Test it locally before deploying (optional but recommended)

You can invoke the Lambda locally with SAM to sanity-check the Bedrock call
before wiring up the frontend:

```bash
sam local invoke ExplainFunction -e events/sample_event.json
```

Create `events/sample_event.json`:

```json
{
  "httpMethod": "POST",
  "body": "{\"document_text\": \"This agreement is made between...\", \"language\": \"English\"}"
}
```

## Notes for the demo

- **PDF uploads**: the current frontend accepts `.txt` directly and asks for
  pasted text otherwise. If you have time on Day 2–3, wire in **Amazon
  Textract** inside `app.py` to pull text from PDF/image uploads via S3 —
  that's a natural "stretch" feature that also strengthens the "AWS at the
  core" judging criterion.
- **Cost**: Bedrock is pay-per-token; a rental agreement (a few thousand
  words) costs a fraction of a cent per explanation. Your $100 in AWS
  credits comfortably covers a full weekend of demoing.
- **Judging tie-in**: in your 3-minute demo, name the services explicitly —
  Bedrock for the explanation, Lambda + API Gateway for the backend, Amplify
  for the live URL. That maps directly onto "Built on AWS" being worth the
  most in judging.
