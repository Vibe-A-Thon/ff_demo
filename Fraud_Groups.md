Below is a **banking fraud taxonomy** that are in use globally

---

## 1) Identity, Onboarding, and Account-Opening Fraud (KYC / CIP fraud)

**Goal:** Open or modify accounts using fake/borrowed identities to later cash out.

* **Synthetic identity fraud** (SSN fragments + fabricated persona)
* **Stolen identity** (full ID takeover)
* **Document forgery** (ID/passport/visa, utility bills, bank statements)
* **Deepfake / liveness bypass** (face/voice spoofing for eKYC)
* **Mule account onboarding** (paid recruits, coerced victims, “money mules”)
* **Business identity fraud** (fake LLCs, forged EIN/beneficial owner data)
* **Account/profile manipulation** (address change, phone/email swap, beneficiary edits)

**U.S. emphasis:** This is often the “front door” to later **ACH/wire/Zelle** push-fraud and **loan fraud**.

---

## 2) Account Takeover (ATO) and Authentication Attacks

**Goal:** Become the customer (or an employee) and transact as them.

* **Credential stuffing / password spraying** (reused passwords)
* **Phishing + MFA fatigue** (push-bombing)
* **SIM swap / port-out** (steal OTPs and reset passwords)
* **Session hijacking** (cookie/token theft, device takeover)
* **Malware / mobile banking trojans** (overlay attacks, ATS)
* **Call-center social engineering** (impersonation to reset access)
* **Third-party/vendor account compromise** (access via fintech integrators)

Regulators expect layered controls and strong authentication governance. ([FFIEC][1])

---

## 3) Social Engineering Scams (Authorized Fraud / APP-style fraud)

**Goal:** Trick the victim into **authorizing** the payment (harder to recover).

* **Impersonation scams** (bank, IRS, police, employer, tech support)
* **Romance scams**
* **Investment scams** (incl. crypto “pig butchering” patterns)
* **Invoice redirection / payment diversion** (vendor bank-details change)
* **Real-estate closing scams** (wire diversion)
* **Refund scams** (fake overpayment + request return)
* **Elder financial exploitation** (manipulation/coercion + transfers) ([FinCEN.gov][2])

**U.S. signal:** Internet-enabled fraud losses are extremely large and rising per FBI IC3 reporting. ([Federal Bureau of Investigation][3])

---

## 4) Card Payment Fraud (Debit/Credit/Prepaid)

**Goal:** Monetize via card-present or card-not-present transactions.

### A) Card-Not-Present (CNP) / E-commerce

* **Stolen card data use**
* **Account testing / BIN attacks**
* **Subscription & digital goods fraud**
* **3DS/OTP interception**
* **Chargeback / “friendly fraud”**

### B) Card-Present / Counterfeit

* **Skimming/shimming** (POS/ATM)
* **Counterfeit cards**
* **Lost/stolen physical card**
* **Merchant collusion / refund abuse**

---

## 5) ACH Fraud (U.S.-heavy)

ACH is a major U.S. rail; fraud shows up as both **unauthorized debits** and **credit-push diversion**.

* **Unauthorized ACH debit** (consumer accounts hit without valid authorization)
* **ACH credit push fraud** (victim *sends* to attacker after deception/ATO)
* **Payroll diversion** (HR/payroll portal compromise → new bank details)
* **Account validation abuse** (micro-deposits, account probing)
* **Corporate ACH fraud** (compromised treasury workstations)

Nacha continues tightening return timing and risk expectations around unauthorized debits. ([Nacha][4])

---

## 6) Wire Transfer Fraud (Domestic + SWIFT)

**Goal:** High-value, fast, often hard to recall.

* **Business Email Compromise (BEC)** (vendor/customer payment redirection)
* **CEO/CFO fraud** (urgent payment instruction spoof)
* **SWIFT-related compromise** (where applicable)
* **Real-estate wire diversion**
* **Trade finance instruction manipulation**

BEC and related schemes are consistently a top, high-loss category in U.S. incident reporting. ([Internet Crime Complaint Center][5])

---

## 7) Instant Payments & P2P (U.S.: Zelle, RTP, FedNow)

**Goal:** “Irreversible-like” instant transfers + social engineering.

* **P2P payment scams** (buyer/seller, impersonation, fake support)
* **ATO + instant cash-out**
* **Mule networks** (rapid layering across accounts)
* **First-payment fraud** (new payee + immediate transfer)

The Federal Reserve explicitly highlights fraud risk considerations for instant payments and urges proactive controls. ([FedNow Explorer][6])

---

## 8) Check Fraud (Still very U.S.-relevant)

**Goal:** Exploit paper instruments and deposit channels.

* **Check theft (mailbox, carrier interception)**
* **Check washing** (alter payee/amount)
* **Counterfeit checks**
* **Remote Deposit Capture (RDC) duplicate deposits**
* **Overpayment check scams** (classic social engineering + returns)

---

## 9) Loan, Credit, and Lending Fraud

**Goal:** Obtain credit and default (“bust-out”) or refinance/cash-out.

* **Personal loan fraud** (synthetic/stolen ID)
* **Credit card application fraud**
* **Mortgage fraud** (income/asset/occupancy misrep)
* **Auto loan fraud** (straw buyers, fake docs)
* **SME/merchant cash advance fraud**
* **BNPL abuse** (where offered)
* **Bust-out fraud** (build trust → max out → disappear)

---

## 10) Merchant / Acquirer / Transaction Laundering Fraud

**Goal:** Abuse merchant onboarding and settlement.

* **Fake merchants** (no real goods/services)
* **Transaction laundering** (processing for hidden merchants)
* **Refund abuse / return fraud**
* **Excessive chargeback manipulation**
* **Promo/offer abuse** (stacking, cycling identities)

---

## 11) Insider, Collusion, and Operational Fraud

**Goal:** Abuse internal access or collude with outsiders.

* **Employee embezzlement**
* **Teller/branch fraud** (cash misappropriation, override abuse)
* **Account manipulation** (fee reversals, limit changes)
* **Collusion rings** (insider + mule + external fraudster)
* **Back-office process fraud** (reconciliations, settlements)

---

## 12) AML-Financial Crime (Often intertwined with fraud)

**Goal:** Move/clean proceeds; hide origin/beneficiary.

* **Money mule networks**
* **Layering/structuring**
* **Sanctions evasion typologies**
* **Crypto on/off-ramp laundering**
* **Trade-based money laundering (TBML)**

---

# “USA-emphasis” cheat sheet: fraud grouped by U.S. payment rails

* **Cards:** CNP, counterfeit, chargebacks
* **ACH:** unauthorized debits, payroll diversion, corporate ACH compromise (Nacha rules + returns matter) ([Nacha][4])
* **Wires:** BEC, invoice diversion, real-estate closing fraud ([Internet Crime Complaint Center][5])
* **Checks:** theft/washing/counterfeit + RDC duplication
* **P2P/Instant:** Zelle/RTP/FedNow scam + ATO cash-out (instant fraud risk called out by Fed resources) ([FedNow Explorer][6])
* **Scams at scale:** IC3 reports massive aggregate internet-crime losses and persistent high-impact categories ([Federal Bureau of Investigation][3])
* **Vulnerable populations:** elder exploitation is a defined, tracked typology with red flags and patterns ([FinCEN.gov][2])

---

[1]: https://www.ffiec.gov/sites/default/files/media/press-releases/2021/authentication-and-access-to-financial-institution-services-and-systems.pdf?utm_source=chatgpt.com "Authentication and Access to Financial Institution Services ..."
[2]: https://www.fincen.gov/system/files/advisory/2022-06-15/FinCEN%20Advisory%20Elder%20Financial%20Exploitation%20FINAL%20508.pdf?utm_source=chatgpt.com "Advisory on Elder Financial Exploitation"
[3]: https://www.fbi.gov/news/press-releases/fbi-releases-annual-internet-crime-report?utm_source=chatgpt.com "FBI Releases Annual Internet Crime Report"
[4]: https://www.nacha.org/rules/risk-management-topics-october-1-2024?utm_source=chatgpt.com "RISK MANAGEMENT TOPICS – October 1, 2024"
[5]: https://www.ic3.gov/AnnualReport/Reports/2024_IC3Report.pdf?utm_source=chatgpt.com "1 2024 IC3 ANNUAL REPORT"
[6]: https://explore.fednow.org/resources/fraud-at-a-glance.pdf?utm_source=chatgpt.com "FedNow® Readiness Guide - Managing Fraud Risk"