# 📑 Comprehensive Due Diligence and Investment Fraud Detection Framework

This framework provides a standardized method to assess the legitimacy and risk of domestic or international business offers. It is designed to be easily referenced, adapted, and used in AI tools, manual checklists, or human evaluations.

---

## 🔍 PURPOSE

To determine whether a business transaction or offer is:

* Legitimate and worth pursuing
* Suspicious and needs further verification
* Likely fraudulent and should be avoided

---

## 📄 INPUT REQUIRED

* Scanned or digital version of the offer or contract
* Known details of the offering party
* Commodity or asset being traded or sold
* Country of origin and destination
* Any available supporting documents

---

## 📊 STANDARD REPORT STRUCTURE

Each review should be structured as follows:

### 1. 🧾 Summary of Document

* Who is offering the deal?
* What is being offered (product/asset)?
* Quantity and pricing
* Payment method and terms
* Country of origin and delivery
* Delivery type (e.g., FOB, CIF)

### 2. 🧪 Risk and Due Diligence Assessment

#### 2.1 Entity Legitimacy & Contact Info

* Is the email domain professional (not Gmail/Yahoo)?
* Does the business have a website?
* Are the address and phone number verifiable?
* Is the company registered in the host country?
* Any visible online reputation or presence?

#### 2.2 Deal Structure and Commercial Terms

* Does pricing align with market rates?
* Are payment methods traceable and secure? (Bank vs Crypto vs Hawala)
* Who bears costs of export, taxes, royalties?
* Are terms vague or overly generous?

#### 2.3 Legal and Compliance Review

* Are licenses, permits, or registration certificates included?
* Are anti-money laundering (AML), KYC, or sanctions considerations addressed?
* Is the offer signed or legally binding?

#### 2.4 Documentation Promised vs Attached

* Certificate of Origin
* Certificate of Ownership
* Bill of Lading or Export Permit
* Invoices or tax certificates
* Were any documents provided up front?

#### 2.5 Reputation and Background Check

* Business name searchable on government databases?
* Company listed in any trade registry?
* Any media coverage or complaints?

---

### 3. 🧠 Fraud Indicators Table

| Indicator                        | Red Flag |
| -------------------------------- | -------- |
| Free email address               | ✅        |
| No business website              | ✅        |
| Unverifiable physical address    | ✅        |
| Crypto or hawala payment only    | ✅✅       |
| Vague or recycled FCO wording    | ✅        |
| No attached verification docs    | ✅        |
| Buyer responsible for everything | ✅        |
| No escrow or LC mentioned        | ✅✅       |

---

### 4. 🏁 Final Assessment

State one of the following:

* **🟥 Likely Fraudulent – DO NOT PROCEED**
* **🟧 High Risk – Caution and Further Verification Required**
* **🟨 Moderate Risk – Proceed with Safeguards**
* **🟩 Low Risk – Reasonable to Proceed with Due Process**

---

### 5. ✅ Recommendations

Always offer specific next steps such as:

* Request company registration docs
* Demand verification from local embassy or law firm
* Insist on escrow or Letter of Credit
* Perform local due diligence
* Contact National Minerals Agency (if applicable)

---

## 🧠 Optional AI Prompt Template

```plaintext
I am reviewing a business offer document and need a professional due diligence analysis. Please assess the document using a business investment and fraud risk framework. Use the following structure:

1. Summary of document
2. Entity legitimacy
3. Deal terms
4. Compliance gaps
5. Reputation and documentation review
6. Fraud indicators table
7. Final assessment
8. Recommendations

Be professional, specific, and clear. Use structured headers. This document may involve commodities like gold, oil, property, or other assets.
```

---

## 📂 Suggested Folder Structure (if hosting on GitHub)

```
/due-diligence-framework
├── README.md  ← summary of use case and how to use
├── framework.md ← this file
├── ai_prompt_template.txt
├── checklists
│   ├── gold_trade_checklist.pdf
│   ├── real_estate_offer_checklist.pdf
│   └── oil_contract_checklist.pdf
└── examples
    ├── example_analysis_gold_offer.md
    └── example_analysis_property_scam.md
```

---

## 🛡️ Maintainers’ Note

This framework is maintained for use in fraud prevention, cross-border trade evaluation, and investor protection. Updates can be made to include new fraud patterns, regulatory requirements, and AI assessment tools.
