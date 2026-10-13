## Non Profit (Frappe/ERPNext v16, Australian edition)

Memberships, donations, volunteers, chapters and grant applications for not-for-profit organisations, built on ERPNext.

This branch (`version-16`) works with **Frappe and ERPNext 16.50 or later** on the version 16 line.

### What's included

- **Members and memberships**: membership types with fees, membership periods (monthly, quarterly, yearly, or the Australian financial year to 30 June), renewals, automatic expiry, and a member summary showing status, expiry date and "member since". Members link to Contacts and to an ERPNext Customer for invoicing.
- **Membership invoicing**: Sales Invoices from memberships, with an optional Sales Taxes and Charges Template (for example `AU Sales - GST`) for GST-registered organisations, and an optional automatic Payment Entry.
- **Donors and donations**: Australian tax deductibility rules built in:
  - gifts, fundraising event contributions and auction contributions
  - the ATO minor-benefit test for contributions (more than $150, benefit no more than the lesser of 20% and $150)
  - deductible amount and financial year (for example `2025-26`) stored on each donation
  - a Journal Entry (debit bank or cash, credit donation income) when a paid donation is submitted; donations carry no GST
- **Australian Donation Receipt** print format that meets the ATO receipt requirements (organisation name, ABN, and a statement that the receipt is for a gift or contribution), with optional emailing on submit.
- **Tax Deductible Donations** report: totals per donor for a financial year, for annual tax statements.
- **Expiring Memberships** report.
- **Volunteers, chapters and grant applications**, as in the original app.
- **v16 navigation**: an Apps screen tile, a Non Profit sidebar and workspace, and a desktop icon for sites still using the icon grid.

Removed from the original app: the India-specific parts (80G certificates, PAN numbers, Razorpay subscriptions and webhooks), Frappe's own consultant certification doctypes, and the Payment Entry override, which conflicted with ERPNext v16.

### Installation

```bash
cd ~/frappe-bench
bench get-app https://github.com/craig-hpc/non_profit --branch version-16
bench --site your-site install-app non_profit
bench build --app non_profit
bench --site your-site migrate
```

### Setup

1. **Company** → *Not-for-profit Registration (Australia)*: enter your **ABN**, and tick **Endorsed as a Deductible Gift Recipient** if you are a DGR. If gifts go to a separate public fund, enter its name.
2. **Non Profit Settings**:
   - *Memberships*: billing cycle, invoicing company, receivable account, payment account, and a GST template if you charge GST on fees.
   - *Donations*: tick *Create Journal Entry for Paid Donations*, then set the *Deposit To* account and the *Donation Income Account*. Optionally turn on emailed receipts.
3. **Membership Type**: create one per membership class, with its fee and a non-stock service **Linked Item** for invoicing.
4. Give staff the **Non Profit Manager** role. The Non Profit tile appears on the Apps screen for users with a Non Profit role or read access to members, memberships, donors or donations.

### Notes

- Receipts and deductibility follow ATO guidance as of 2026. Check current ATO rules for your organisation, especially for fundraising events and auctions.
- The deductible amount is only worked out when the donation's company is marked as a DGR.

### License

MIT
