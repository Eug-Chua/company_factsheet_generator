"""
Prompt Builder
Builds prompts for LLM and parses responses
"""

import re
from typing import List, Dict


class PromptBuilder:
    """Builds prompts and parses LLM responses"""

    def __init__(self, logger):
        """Initialize prompt builder"""
        self.logger = logger

    def _prepare_context(self, relevant_chunks: List[Dict]) -> str:
        """Prepare context from chunks"""
        context_texts = []
        for i, chunk in enumerate(relevant_chunks, 1):
            context_texts.append(f"[Chunk {i} - {chunk['section_header']}]\n{chunk['content']}\n")
        return "\n---\n".join(context_texts)

    def _prepare_questions_text(self, questions: List[Dict]) -> str:
        """Prepare questions as formatted text"""
        return "\n".join([f"{q['number']}. {q['text']}" for q in questions])

    def build_prompt_template(self) -> str:
        """Build comprehensive prompt template for question_set_v3.md"""
        return """You are a senior credit analyst creating a comprehensive credit analysis report from annual report data.

# CATEGORY: {category}

# SOURCE DATA - RELEVANT ANNUAL REPORT SECTIONS

{context}

# QUESTIONS TO ANSWER

{questions_text}

# CRITICAL INSTRUCTIONS

## QUESTION SET STRUCTURE (V3)
This question set has THREE types of questions:

1. **QUALITATIVE (Q1-Q8)**: Business fundamentals, risks, liabilities
2. **DATA EXTRACTION (Q7-Q35)**: Pure retrieval - extract exact figures from financial statements
3. **CALCULATIONS (Q36-Q57)**: Compute metrics using data from previous questions

## LENGTH REQUIREMENTS

**For QUALITATIVE questions (Q1-Q8):**
- 3-5 bullet points maximum
- Include key details, names, relationships
- For conditional questions (Q3a/b, Q5a/b, Q6a/b):
  - Part (a): Answer Yes or No
  - Part (b): Only provide details if (a) is Yes
- If data is missing, state briefly: "Not disclosed in provided context"

**For DATA EXTRACTION questions (Q7-Q35):**
- 1-3 bullet points maximum
- Extract EXACT figures from financial statements
- Format: "2024: $5,372M, 2023: $4,835M, 2022: $1,433M"
- DO NOT calculate or derive values - only extract what is explicitly stated
- If not explicitly stated, note: "Not explicitly stated in provided context"

**For CALCULATION questions (Q36-Q57):**
- Show the formula first
- Show your calculation with numbers
- Present final result clearly
- Format: "**Formula**: FCF = Operating Cash Flow - Capex\\n**Calculation**: $852M - $113M = **$739M**"

## DATA EXTRACTION GUIDELINES

**PART 2: DATA EXTRACTION (Q7-Q35) - NO CALCULATIONS**

1. **Find the official financial statements:**
   - Income Statement: "Consolidated Income Statement" or "Statement of Profit or Loss"
   - Cash Flow: "Consolidated Cash Flow Statement" or "Statement of Cash Flows"
   - Balance Sheet: "Consolidated Balance Sheet" or "Statement of Financial Position"

2. **Extract ONLY explicitly stated figures:**
   - Look for the exact line item (e.g., "Revenue", "Operating Income", "Total Debt")
   - Extract the number as shown in the statement
   - If a line item like "Gross Profit" doesn't exist, state: "Not explicitly stated"
   - DO NOT calculate derived metrics in this section

3. **Handle missing data:**
   - If 2022 data not available: "2024: $X, 2023: $Y, 2022: Data not available"
   - If entire metric missing: "Data not available in provided context"

## CALCULATION GUIDELINES

**PART 3: CALCULATED METRICS (Q36-Q57) - SHOW YOUR WORK**

For calculation questions, ALWAYS:
1. State the formula
2. Show the calculation with actual numbers
3. Present the final result clearly

**Common formulas:**
- Gross Profit Margin = (Revenue - Cost of Revenue) / Revenue × 100%
- Operating Margin = Operating Income / Revenue × 100%
- EBITDA Margin = EBITDA / Revenue × 100%
- Net Margin = Net Income / Revenue × 100%
- YoY Growth = (Current Year - Prior Year) / Prior Year × 100%
- CAGR = ((Ending / Beginning)^(1/Years) - 1) × 100%
- Free Cash Flow = Operating Cash Flow - Capex
- Net Debt = Total Debt - Cash
- Net Debt/EBITDA = Net Debt / EBITDA
- Interest Coverage = EBITDA / Interest Expense
- Current Ratio = Current Assets / Current Liabilities
- Quick Ratio = (Current Assets - Inventory) / Current Liabilities
- DSO = (Trade Receivables / Revenue) × 365
- ROA = Net Income / Total Assets × 100%
- ROE = Net Income / Total Equity × 100%

## DATA QUALITY RULES
1. Use ONLY data from provided context
2. For DATA EXTRACTION: Do not calculate or derive - only extract explicit values
3. For CALCULATIONS: Reference the source questions (e.g., "Using Q7 and Q8...")
4. If data is missing, clearly state what's missing
5. Do NOT make up numbers

## OUTPUT FORMAT EXAMPLES

**QUALITATIVE (with conditional):**
**Question 3: Does the company disclose government ownership? (Yes/No)**
- Yes

**Question 4: If yes to Q3, describe the government relationships:**
- Temasek Holdings (sovereign wealth fund) holds 18% stake
- Two board members: Former Minister of Finance (advisory role), Ex-MAS director
- No joint ventures with government entities disclosed

**DATA EXTRACTION:**
**Question 10: What is total revenue for fiscal years 2024, 2023, and 2022?**
- 2024: $2,797M, 2023: $2,359M, 2022: $1,433M

**Question 12: What is gross profit for fiscal years 2024, 2023, and 2022?**
- Not explicitly stated in financial statements (shows Revenue and Cost of Revenue separately)

**CALCULATION:**
**Question 39: Calculate gross profit and gross profit margin for 2024, 2023, 2022**
- **Formula**: Gross Profit = Revenue - Cost of Revenue; Margin = (Gross Profit / Revenue) × 100%
- **2024**: $2,797M - $1,623M = $1,174M; Margin = 42.0%
- **2023**: $2,359M - $1,499M = $860M; Margin = 36.5%
- **2022**: $1,433M - $1,356M = $77M; Margin = 5.4%

**Question 47: Calculate free cash flow for 2024, 2023, 2022**
- **Formula**: FCF = Operating Cash Flow - Capital Expenditure
- **2024**: $852M - $113M = **$739M**
- **2023**: $1,187M - $92M = **$1,095M**
- **2022**: $(682)M - $190M = **$(872)M**

# START ANSWERING

Answer ALL questions using the provided context. Follow the guidelines for each question type."""

    def build_batch_prompt(self, category: str, questions: List[Dict],
                          relevant_chunks: List[Dict]) -> str:
        """Build prompt for batch question answering"""
        template = self.build_prompt_template()
        context = self._prepare_context(relevant_chunks)
        questions_text = self._prepare_questions_text(questions)
        return template.format(category=category, context=context,
                             questions_text=questions_text)

    def _parse_with_regex(self, response_text: str):
        """Parse response using regex pattern"""
        pattern = r'\*\*Question (\d+):[^\n]*\*\*\s*(.*?)(?=\*\*Question \d+:|\Z)'
        return re.findall(pattern, response_text, re.DOTALL)

    def _convert_matches_to_dict(self, matches):
        """Convert regex matches to answer dictionary"""
        answers = {}
        for q_num_str, answer_text in matches:
            q_num = int(q_num_str)
            answers[q_num] = answer_text.strip()
            self.logger.debug(f"  Q{q_num}: {len(answer_text)} chars")
        return answers

    def _fallback_parse(self, response_text: str, questions: List[Dict]):
        """Fallback parsing if regex fails"""
        self.logger.warning("Batch parsing failed, using fallback")
        answers = {}
        parts = response_text.split('\n\n')
        for i, q in enumerate(questions):
            if i < len(parts):
                answers[q['number']] = parts[i].strip()
        return answers

    def parse_batch_response(self, response_text: str, questions: List[Dict]) -> Dict[int, str]:
        """Parse batch response into individual answers"""
        matches = self._parse_with_regex(response_text)
        self.logger.debug(f"Parsed {len(matches)} answers from LLM response")
        if matches:
            return self._convert_matches_to_dict(matches)
        return self._fallback_parse(response_text, questions)

    def build_single_answer_prompt(self, question: str, question_num: int,
                                   context: str) -> str:
        """Build prompt for single question answer"""
        return f"""You are analyzing an annual report to answer credit analysis questions.

Question {question_num}: {question}

Here are the most relevant sections from the annual report:

{context}

Instructions:
1. Answer the question based ONLY on the provided context
2. Be specific and include numbers/data points when available
3. If information is not available in the context, clearly state what's missing
4. Structure your answer with bullet points
5. Keep the answer concise

Answer:"""
