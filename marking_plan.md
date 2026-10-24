# Marking plan

Circle each item in red on the page in `real_forms_marked/`. `Expected` is what a correct pipeline must return.
This file is generated from `data/ground_truth/` — edit those files, then rerun `python tools/make_marking_plan.py`.

## 01_text_typed_report_airliner_air_study.png

| # | Where | How | Expected |
|---|---|---|---|
| 01-1 | "Germantown" (last line of BACKGROUND: "Germantown MD, performed the study") | circle | Germantown |
| 01-2 | "smoking" in "the period when smoking was banned on" (BACKGROUND) | circle | smoking |
| 01-3 | "92" in "total of 92 flights" | tight circle | 92 |
| 01-4 | "unobtrusive" in "small, unobtrusive instruments" | circle | unobtrusive |

## 02_text_typed_lab_report.png

| # | Where | How | Expected |
|---|---|---|---|
| 02-1 | "D. M. Teng" (PROJECT LEADER value) | circle | D. M. Teng |
| 02-2 | "1901" (CHARGE NUMBER value) | circle | 1901 |
| 02-3 | "50-liter" at the start of the line after "...functioning satisfactorily. Three" | tight circle | 50-liter |
| 02-4 | "20 hours" in "Denitrification was accomplished in 20 hours" | loose circle | 20 hours |
| 02-5 | "pH" in the noisy last paragraph ("A portion of the pH profile") | open circle (leave a gap) | pH |

## 03_text_article_serif_with_italics.png

| # | Where | How | Expected |
|---|---|---|---|
| 03-1 | "Circulation" in the body ("journal Circulation Kawachi"), NOT the byline | circle | Circulation |
| 03-2 | "32,000" | circle | 32,000 |
| 03-3 | "statistical bias" in the italic quote | circle | statistical bias |
| 03-4 | "NADA" in "NONE, NOTHING, ZERO, NADA, NIL" | open circle (leave a gap) | NADA |
| 03-5 | "Rosenblatt" in "Stanley Rosenblatt" (2nd paragraph) | loose circle that spills onto the line above | Rosenblatt |
| 03-6 | "SMOKERS!" (last paragraph) | double circle (two loops) | SMOKERS |

## 04_text_two_column_journal_page.png

| # | Where | How | Expected |
|---|---|---|---|
| 04-1 | "Framingham" in the byline (under author name), NOT the body | circle | Framingham |
| 04-2 | "325,000" (left column) | circle | 325,000 |
| 04-3 | "THE CARDIOVASCULAR HAZARDS" (heading, right column) | one long circle around the heading | THE CARDIOVASCULAR HAZARDS |
| 04-4 | "$19 billion" (left column) | tight circle | $19 billion |
| 04-5 | "Boston" in the footnote at bottom left | circle | Boston |
| 04-6 | "inhale." (end of a right-column paragraph) | circle | inhale |

## 05_text_memo_serif_with_bullets.png

| # | Where | How | Expected |
|---|---|---|---|
| 05-1 | "Kevin Sweeney" | circle | Kevin Sweeney |
| 05-2 | "MARCH 11, 1996" (header date) | circle | MARCH 11, 1996 |
| 05-3 | "weak" in "controls are very weak" | tight circle | weak |
| 05-4 | "toxic waste" | circle | toxic waste |
| 05-5 | "Bacon" in "Shook, Hardy & Bacon" | tight circle touching "Hardy" | Bacon |

## 06_text_memo_key_findings_bullets.png

| # | Where | How | Expected |
|---|---|---|---|
| 06-1 | "24.4%" | circle | 24.4% |
| 06-2 | "Marlboro" | circle | Marlboro |
| 06-3 | "not" (already underlined: "there is not a problem") | tight circle | not |
| 06-4 | "4.6%" (first bullet) | circle | 4.6% |
| 06-5 | "(BIAD #93-13104)" under SUBJECT | circle | BIAD #93-13104 |
| 06-6a | "18.5%" and "76%" | circle each | 18.5% |
| 06-6b | "18.5%" and "76%" | circle each | 76% |

## 07_text_typewriter_qa_document.png

| # | Where | How | Expected |
|---|---|---|---|
| 07-1 | "TDK" | circle | TDK |
| 07-2 | "Pittsburgh," | circle | Pittsburgh |
| 07-3 | the whole bold sentence "How often are you going to have theme nights?" | one loose loop around the sentence | How often are you going to have theme nights? |
| 07-4 | "21" in "at least 21 years of age" | tight circle | 21 |
| 07-5 | "Cleveland" | double circle (two loops) | Cleveland |
| 07-6 | "Approved" in the top line "4/24/89 - Approved", NOT the footer | circle | Approved |

## 08_text_bold_typewriter_memo.png

| # | Where | How | Expected |
|---|---|---|---|
| 08-1 | "FUBYAS" | circle | FUBYAS |
| 08-2 | "22-25" | circle | 22-25 |
| 08-3 | "Whitaker Park" | circle | Whitaker Park |
| 08-4 | "Promotion" in "(MDD, Brand, Media, Promotion)" | tight circle touching "Media" | Promotion |
| 08-5 | "absurdity," | open circle (leave a gap) | absurdity |
| 08-6 | "punk" (last line) | circle | punk |

## 09_text_memo_with_name_lists.png

| # | Where | How | Expected |
|---|---|---|---|
| 09-1 | "E. Merlo" (Distribution list) | circle | E. Merlo |
| 09-2 | "C. Purcell" in the cc list, NOT "Clare Purcell" in the body | circle | C. Purcell |
| 09-3 | "August 16" | circle | August 16 |
| 09-4a | "J. Nelson" and "S. Parrish" (two lines) | ONE circle around both names | J. Nelson |
| 09-4b | "J. Nelson" and "S. Parrish" (two lines) | ONE circle around both names | S. Parrish |
| 09-5 | "Appendix A" in "listed in Appendix A of the PM", NOT the last line | circle | Appendix A |
| 09-6 | "10017-5592" (header address) | circle | 10017-5592 |

## 10_text_memo_with_number_tables.png

| # | Where | How | Expected |
|---|---|---|---|
| 10-1 | "135" (San Diego row, LATEST QUARTER, INDEX TO U.S.) | circle | 135 |
| 10-2 | "-3.92" (Glendale row, LATEST QUARTER, PT CHG) | circle | -3.92 |
| 10-3 | "Montclair Ultra KS" (row label, packing table) | circle | Montclair Ultra KS |
| 10-4 | ".25" in the Montclair Lt. 100 row (CUR QTR), NOT the row above | circle | .25 |
| 10-5 | "102" (L.A. So. row, already underlined) | tight circle | 102 |
| 10-6 | "Anaheim" (division name) | circle | Anaheim |

## 11_options_interview_with_code_tables.png

| # | Where | How | Expected |
|---|---|---|---|
| 11-qA_29 | Q.A, PRODUCT #29 column: code "10- 1" (row "None (did not smoke any)") | circle the code | None (did not smoke any) |
| 11-qA_43 | Q.A, PRODUCT #43 column: code "4" (row "3 or 4 packs") | circle the code | 3 or 4 packs |
| 11-qB | Q.B | leave blank | (none — leave blank) |
| 11-qC | Q.C: the words "Wasn't home" (not its number) | circle the label | Wasn't home |
| 11-qD | Q.D: "Yes" (box at right) | circle touching the No row | Yes |

## 12_options_dense_screener_brand_codes.png

| # | Where | How | Expected |
|---|---|---|---|
| 12-qA | Q.A: "No....2" | circle | No |
| 12-qB | Q.B: "25 - 34....2" | circle | 25-34 |
| 12-qC | Q.C | leave blank | (none — leave blank) |
| 12-qD | Q.D: "Yes....1" | circle | Yes |
| 12-qE | Q.E: "King Size (85mm-95mm)....2" | tight circle | King Size (85mm-95mm) |
| 12-qF | Q.F: "Real....-7" in the MIDDLE column (Kent in the first column has the same code -7) | circle | Real |
| 12-qG | Q.G: "Male Full-Flavor....3" | circle | Male Full-Flavor |

## 13_options_report_form_scoreboard_yes_no.png

| # | Where | How | Expected |
|---|---|---|---|
| 13-q1 | Q1 scoreboard: 4th box from the right (BEST end) | circle the box | 18 |
| 13-q5a | Q5a: the "No" box | circle the box | No |
| 13-q5b | Q5b | leave blank | (none — leave blank) |
| 13-q6a | Q6a: the word "Bitter" (not its box) | circle the word | Bitter |
| 13-q6b | Q6b: the box next to "About right" | circle the box | About right |

## 14_options_two_column_yes_no_questionnaire.png

| # | Where | How | Expected |
|---|---|---|---|
| 14-sex | Header: "Male" | circle | Male |
| 14-q1a | Q1a hay fever: blank line under YES | circle the blank | YES |
| 14-q1b | Q1b asthma: blank line under NO | circle the blank | NO |
| 14-q1c | Q1c, Q1d, Q1e | leave blank | (none — leave blank) |
| 14-q1d | Q1c, Q1d, Q1e | leave blank | (none — leave blank) |
| 14-q1e | Q1c, Q1d, Q1e | leave blank | (none — leave blank) |
| 14-q3 | Q3 Do you smoke?: blank line under NO | circle the blank | NO |
| 14-q8a | Q8a eyes and Q8d throat: blank lines under YES (8b, 8c blank) | circle each blank | YES |
| 14-q8b | Q8a eyes and Q8d throat: blank lines under YES (8b, 8c blank) | circle each blank | (none — leave blank) |
| 14-q8c | Q8a eyes and Q8d throat: blank lines under YES (8b, 8c blank) | circle each blank | (none — leave blank) |
| 14-q8d | Q8a eyes and Q8d throat: blank lines under YES (8b, 8c blank) | circle each blank | YES |
| 14-q12a | Q12a: blank under YES; Q12b: blank under NO; Q12c blank | circle the blanks | YES |
| 14-q12b | Q12a: blank under YES; Q12b: blank under NO; Q12c blank | circle the blanks | NO |
| 14-q12c | Q12a: blank under YES; Q12b: blank under NO; Q12c blank | circle the blanks | (none — leave blank) |

## 15_options_focus_group_screener.png

| # | Where | How | Expected |
|---|---|---|---|
| 15-q1a | Q1.a: "Yes" | circle | Yes |
| 15-q2 | Q2: "An automobile manufacturer" and "A food processor" | circle each | An automobile manufacturer · A food processor |
| 15-q3a | Q3.a: "25-34" | circle | 25-34 |
| 15-q4b | Q4.b: "100mm" | circle | 100mm |
| 15-q4c | Q4.c: "Filter," only (NOT "Non-Filter") | tight circle | Filter |
| 15-q4d | Q4.d: "Non-Menthol" | circle | Non-Menthol |
| 15-q4e | Q4.e | leave blank | (none — leave blank) |

## 16_options_screener_dotted_codes.png

| # | Where | How | Expected |
|---|---|---|---|
| 16-q1 | Q1: "An insurance company (CONTINUE)....3" | circle | An insurance company |
| 16-q2 | Q2: "Female....2" | circle | Female |
| 16-q3a | Q3a: "Soft Drinks....2" | circle | Soft Drinks |
| 16-q3b | Q3b: "No (CONTINUE)....1" | loose circle | No |
| 16-q4 | Q4: only the code digit "1" at the end of the Yes line | small circle on the digit | Yes |
| 16-q5a | Q5a | leave blank | (none — leave blank) |
| 16-q5b | Q5b: "Non-Menthol (CONTINUE)....1" | circle | Non-Menthol |
| 16-q5c | Q5c | leave blank | (none — leave blank) |
| 16-q6 | Q6: "31-40....2" | circle | 31-40 |

## 17_options_inquiry_with_lettered_choices.png

| # | Where | How | Expected |
|---|---|---|---|
| 17-II_3 | II.3: "b) Intergroup work" and "d) Liaison with other organizations" | circle each | b) Intergroup work · d) Liaison with other organizations |
| 17-II_4 | II.4: "c) Its rules of procedure" | open circle (leave a gap) | c) Its rules of procedure |

## 18_options_phone_survey_yes_no_codes.png

| # | Where | How | Expected |
|---|---|---|---|
| 18-q1 | Q1: the code "1" next to Yes | circle the code | Yes |
| 18-q2 | Q2: the word "No" | circle the word | No |
| 18-time_zone | TIME ZONE: the letter "M" in "E C M P" | small circle | M |
| 18-callback_date | CALLBACK DATE | leave blank | (none — leave blank) |

## 19_options_screener_brackets_age_products.png

| # | Where | How | Expected |
|---|---|---|---|
| 19-sex | Indicate: the bracket next to "Female" | circle the bracket | Female |
| 19-q1 | Q1: the bracket next to "35 - 49" | circle the bracket | 35-49 |
| 19-q2 | Q2: the brackets for "Coffee", "Cigarettes" and "Mouth wash" | circle each bracket | Coffee · Cigarettes · Mouth wash |
| 19-q3b_not_married | Q3b: the "[ ]" after "CHECK HERE IS NOT MARRIED" | circle it | Not married |

## 20_options_health_survey_yes_no_circle.png

| # | Where | How | Expected |
|---|---|---|---|
| 20-q1 | Q1: "YES" | circle | YES |
| 20-q1_2_1 | Q1.2.1 February - June: "NO" | circle | NO |
| 20-q1_2_2 | Q1.2.2 July: "YES" | circle | YES |
| 20-q1_2_3 | Q1.2.3 August - October | leave blank | (none — leave blank) |
| 20-q1_2_4 | Q1.2.4 November - January: "NO" | circle | NO |
| 20-q1_3 | Q1.3: the code "3" | circle the code | Sometimes worse, sometimes better |
