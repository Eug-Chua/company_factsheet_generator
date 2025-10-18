# Credit Analysis Question Set

**Design Philosophy:**
- **Atomic Questions**: One fact per question for clear retrieval targets
- **Separation of Concerns**: Data extraction separate from calculations
- **Existence Checks**: Conditional questions for optional disclosures
- **RAGAS-Friendly**: Each question has one verifiable answer

---

## PART 1: BUSINESS FUNDAMENTALS (Qualitative)

### 1. What industry/sector is the company in?

### 2. What geographic markets does the company operate in? List all countries or regions where the company has significant operations.

### 3. Describe the company's ownership structure and any government relationships, including: government ownership stakes, sovereign wealth fund investments, government-linked board members, or state-owned enterprise relationships. If no such relationships exist, state "No government relationships disclosed in the annual report."

### 4. Does the company disclose revenue breakdown by geography? If yes, provide the specific percentages or amounts by region/country for the most recent fiscal year.

### 5. What are the company's primary revenue streams and business model as described in the annual report?

### 6. List the top 5 most significant risks highlighted by management in the annual report's risk factors or principal risks section. If no dedicated risk section exists, state "No dedicated risk section found in the annual report."

### 7. Describe any material legal proceedings, regulatory investigations, or environmental liabilities disclosed in the annual report, including estimated amounts where available. If none are disclosed, state "No material legal proceedings or liabilities disclosed."

### 8. What is the company's total dividend payout or dividend per share for fiscal year 2024? If no dividends were paid or disclosed, state "No dividends disclosed."

### 9. Describe the company's capital allocation strategy and priorities as stated in the annual report (e.g., dividends, buybacks, debt reduction, growth investments). If not explicitly discussed, state "Capital allocation strategy not explicitly discussed."

---

## PART 2: FINANCIAL DATA EXTRACTION (Quantitative - Pure Retrieval)

*Instructions: Extract exact figures from financial statements. If data is not available, state "Data not available in provided context".*

### INCOME STATEMENT DATA

### 10. What is total revenue for fiscal years 2024, 2023, and 2022?

### 11. What is cost of revenue (or cost of goods sold/COGS) for fiscal years 2024, 2023, and 2022?

### 12. What is gross profit for fiscal years 2024, 2023, and 2022? (If not explicitly stated, note: "Not explicitly stated - needs calculation")

### 13. What is operating income (or EBIT) for fiscal years 2024, 2023, and 2022?

### 14. What is EBITDA (or Adjusted EBITDA) for fiscal years 2024, 2023, and 2022? (If not explicitly stated but operating income is available, note the terminology used)

### 15. What is net income (or net profit) for fiscal years 2024, 2023, and 2022?

### 16. What is interest expense for fiscal years 2024, 2023, and 2022?

### 17. What is income tax expense for fiscal years 2024, 2023, and 2022?

### 18. What is profit before tax for fiscal years 2024, 2023, and 2022?

### CASH FLOW DATA

### 19. What is cash from operating activities (operating cash flow) for fiscal years 2024, 2023, and 2022?

### 20. What is capital expenditure (capex or purchase of property, plant & equipment) for fiscal years 2024, 2023, and 2022?

### 21. What is depreciation and amortization expense for fiscal years 2024, 2023, and 2022?

### 22. What is cash from investing activities for fiscal years 2024, 2023, and 2022?

### 23. What is cash from financing activities for fiscal years 2024, 2023, and 2022?

### BALANCE SHEET - ASSETS

### 24. What is total assets for fiscal years 2024, 2023, and 2022?

### 25. What is total current assets for fiscal year 2024?

### 26. What is total non-current assets for fiscal year 2024?

### 27. What is cash and cash equivalents for fiscal years 2024, 2023, and 2022?

### 28. What is trade receivables (or accounts receivable) for fiscal year 2024?

### 29. What is inventory for fiscal year 2024?

### BALANCE SHEET - LIABILITIES & EQUITY

### 30. What is total liabilities for fiscal year 2024?

### 31. What is total current liabilities for fiscal year 2024?

### 32. What is total non-current liabilities for fiscal year 2024?

### 33. What is total debt (including all borrowings, bonds, and loans - both current and non-current) for fiscal years 2024, 2023, and 2022?

### 34. What is the breakdown of debt into current (short-term) and non-current (long-term) portions for fiscal year 2024?

### 35. What is total equity (or shareholders' equity) for fiscal years 2024, 2023, and 2022?

### DEBT DETAILS

### 36. What types of debt instruments does the company have? (e.g., bank loans, bonds, convertible notes, lease liabilities)

### 37. What is the debt maturity schedule? Provide amounts by maturity period if disclosed (e.g., within 1 year, 1-2 years, 2-5 years, beyond 5 years).

### 38. What proportion of debt is fixed-rate versus floating-rate? If disclosed, provide percentages or amounts.

---

## PART 3: CALCULATED METRICS & RATIOS

*Instructions: Calculate using data from Part 2. Show your calculation formula and work.*

### PROFITABILITY METRICS

### 39. Calculate gross profit and gross profit margin for fiscal years 2024, 2023, and 2022.
**Formula**: Gross Profit = Revenue - Cost of Revenue; Gross Profit Margin = (Gross Profit / Revenue) × 100%
**Use data from**: Q10, Q11, Q12

### 40. Calculate operating profit margin for fiscal years 2024, 2023, and 2022.
**Formula**: Operating Margin = (Operating Income / Revenue) × 100%
**Use data from**: Q10, Q13

### 41. Calculate EBITDA margin for fiscal years 2024, 2023, and 2022.
**Formula**: EBITDA Margin = (EBITDA / Revenue) × 100%
**Use data from**: Q10, Q14

### 42. Calculate net profit margin for fiscal years 2024, 2023, and 2022.
**Formula**: Net Margin = (Net Income / Revenue) × 100%
**Use data from**: Q10, Q15

### 43. Calculate the effective tax rate for fiscal years 2024, 2023, and 2022.
**Formula**: Effective Tax Rate = (Income Tax Expense / Profit Before Tax) × 100%
**Use data from**: Q17, Q18

### GROWTH METRICS

### 44. Calculate year-over-year revenue growth rates for 2024 vs 2023 and 2023 vs 2022.
**Formula**: YoY Growth = ((Current Year - Prior Year) / Prior Year) × 100%
**Use data from**: Q10

### 45. Calculate the 2-year revenue CAGR from 2022 to 2024.
**Formula**: CAGR = ((Ending Value / Beginning Value)^(1/Number of Years) - 1) × 100%
**Use data from**: Q10

### 46. Calculate year-over-year net income growth rates for 2024 vs 2023 and 2023 vs 2022.
**Formula**: YoY Growth = ((Current Year - Prior Year) / Prior Year) × 100%
**Use data from**: Q15

### CASH FLOW METRICS

### 47. Calculate free cash flow (FCF) for fiscal years 2024, 2023, and 2022.
**Formula**: Free Cash Flow = Operating Cash Flow - Capital Expenditure
**Use data from**: Q19, Q20

### 48. Calculate the operating cash flow margin for fiscal years 2024, 2023, and 2022.
**Formula**: OCF Margin = (Operating Cash Flow / Revenue) × 100%
**Use data from**: Q10, Q19

### 49. Calculate the cash conversion rate for fiscal year 2024.
**Formula**: Cash Conversion = (Operating Cash Flow / Net Income) × 100%
**Use data from**: Q15, Q19

### LEVERAGE RATIOS

### 50. Calculate net debt for fiscal years 2024, 2023, and 2022.
**Formula**: Net Debt = Total Debt - Cash and Cash Equivalents
**Use data from**: Q27, Q33

### 51. Calculate the Net Debt/EBITDA ratio for fiscal years 2024, 2023, and 2022.
**Formula**: Net Debt/EBITDA = Net Debt / EBITDA
**Use data from**: Q14, Q50

### 52. Calculate the EBITDA/Interest Expense (interest coverage) ratio for fiscal years 2024, 2023, and 2022.
**Formula**: Interest Coverage = EBITDA / Interest Expense
**Use data from**: Q14, Q16

### 53. Calculate the Debt/Assets ratio for fiscal year 2024.
**Formula**: Debt/Assets = (Total Debt / Total Assets) × 100%
**Use data from**: Q24, Q33

### 54. Calculate the Debt/Equity ratio for fiscal year 2024.
**Formula**: Debt/Equity = Total Debt / Total Equity
**Use data from**: Q33, Q35

### LIQUIDITY RATIOS

### 55. Calculate the Current Ratio for fiscal year 2024.
**Formula**: Current Ratio = Current Assets / Current Liabilities
**Use data from**: Q25, Q31

### 56. Calculate the Quick Ratio (Acid-Test Ratio) for fiscal year 2024.
**Formula**: Quick Ratio = (Current Assets - Inventory) / Current Liabilities
**Use data from**: Q25, Q29, Q31

### EFFICIENCY RATIOS

### 57. Calculate Days Sales Outstanding (DSO) for fiscal year 2024.
**Formula**: DSO = (Trade Receivables / Revenue) × 365
**Use data from**: Q10, Q28

### 58. Calculate inventory turnover for fiscal year 2024 (if applicable for the business).
**Formula**: Inventory Turnover = Cost of Revenue / Inventory
**Use data from**: Q11, Q29

### 59. Calculate Return on Assets (ROA) for fiscal year 2024.
**Formula**: ROA = (Net Income / Total Assets) × 100%
**Use data from**: Q15, Q24

### 60. Calculate Return on Equity (ROE) for fiscal year 2024.
**Formula**: ROE = (Net Income / Total Equity) × 100%
**Use data from**: Q15, Q35

---

