import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Buffett 5-Metric Screener", page_icon="📈", layout="centered")
st.title("5-Metric Screener & Target Prices")
st.caption("Works for US tickers (e.g., AAPL, MSFT) and Canadian tickers (e.g., RY.TO, TD.TO).")

ticker = st.text_input("Enter Ticker Symbol:", value="AAPL").upper().strip()

if st.button("Analyze Stock"):
    try:
        stock = yf.Ticker(ticker)
        
        try:
            info = stock.info
            company_name = info.get("longName") or info.get("shortName") or ticker
        except:
            info = {}
            company_name = ticker
            
        currency = info.get("currency", "USD")
        
        hist = stock.history(period="5d")
        if not hist.empty:
            current_price = hist['Close'].iloc[-1]
        else:
            current_price = 0.00
            
        st.subheader(f"🏢 {company_name} ({ticker})")
        st.metric(label="Current Stock Price", value=f"${current_price:,.2f} {currency}")

        st.write("---")
        st.subheader("📰 Recent Company News")
        
        try:
            news = stock.news
            if news:
                count = 0
                for article in news:
                    if count >= 3:
                        break
                    
                    title = article.get('title') or article.get('content', {}).get('title')
                    raw_link = article.get('link') or article.get('content', {}).get('clickThroughUrl')
                    
                    if isinstance(raw_link, dict):
                        link = raw_link.get('url', '#')
                    else:
                        link = raw_link
                        
                    if title and link:
                        publisher = article.get('publisher', 'Financial News')
                        st.write(f"- **[{title}]({link})**")
                        st.caption(f"Publisher: {publisher}")
                        count += 1
                if count == 0:
                    st.write("No recent articles found.")
            else:
                st.write("No recent news found.")
        except Exception:
            st.write("Could not load news at this time.")

        financials = stock.financials
        balance_sheet = stock.balance_sheet
        cash_flow = stock.cashflow
        
        st.write("---")
        st.subheader("📊 Fundamental Breakdown")

        try:
            rev_series = financials.loc['Total Revenue'].iloc[0:3].iloc[::-1]  
            rev_years = [d.strftime('%Y') for d in rev_series.index]
            rev_values = [v / 1e9 for v in rev_series.values] 
            
            rev_growth_y1 = ((rev_values[1] - rev_values[0]) / rev_values[0]) * 100
            rev_growth_y2 = ((rev_values[2] - rev_values[1]) / rev_values[1]) * 100
            rev_pass = (rev_values[2] > rev_values[1]) and (rev_values[1] > rev_values[0])
            
            with st.expander("1. Revenue Growth (Last 3 Years)", expanded=True):
                if rev_pass:
                    st.success("✅ **PASS: Revenue is consistently climbing.**")
                else:
                    st.error("❌ **FAIL: Revenue growth is flat or declining.**")
                
                df_rev = pd.DataFrame({
                    "Fiscal Year": rev_years,
                    f"Revenue ({currency} Billions)": [f"${v:,.2f}B" for v in rev_values]
                })
                st.table(df_rev)
                st.write(f"• Growth {rev_years[0]} ➔ {rev_years[1]}: **{rev_growth_y1:+.2f}%**")
                st.write(f"• Growth {rev_years[1]} ➔ {rev_years[2]}: **{rev_growth_y2:+.2f}%**")
        except:
            st.error("Missing Revenue Data on Yahoo Finance.")
            rev_pass = False; rev_growth_y2 = 5

        try:
            raw_net_income = financials.loc['Net Income'].iloc[0]
            net_income = raw_net_income / 1e9
            latest_rev = rev_values[-1]
            net_margin = (net_income / latest_rev) * 100
            margin_pass = net_margin >= 15.0

            with st.expander("2. Net Profit Margin", expanded=True):
                if margin_pass:
                    st.success(f"✅ **PASS: Margin is {net_margin:.2f}% (Target: >15%).** Strong pricing power.")
                else:
                    st.error(f"❌ **FAIL: Margin is {net_margin:.2f}% (Target: >15%).** Low profitability.")
                st.write(f"• Most Recent Annual Revenue: **${latest_rev:,.2f}B**")
                st.write(f"• Most Recent Net Income: **${net_income:,.2f}B**")
                st.write(f"• Exact Net Margin: **{net_margin:.2f}%**")
        except:
            st.error("Missing Margin Data on Yahoo Finance.")
            margin_pass = False; raw_net_income = 0

        try:
            total_debt = (balance_sheet.loc['Total Debt'].iloc[0] if 'Total Debt' in balance_sheet.index else balance_sheet.loc['Long Term Debt'].iloc[0]) / 1e9
            total_cash = balance_sheet.loc['Cash And Cash Equivalents'].iloc[0] / 1e9
            debt_ratio = total_debt / total_cash if total_cash > 0 else 999.0
            debt_pass = debt_ratio < 3.0

            with st.expander("3. Debt-to-Cash Safety", expanded=True):
                if debt_pass:
                    st.success(f"✅ **PASS: Debt is {debt_ratio:.2f}x Cash (Target: <3x).** Safe balance sheet.")
                else:
                    st.error(f"❌ **FAIL: Debt is {debt_ratio:.2f}x Cash (Target: <3x).** Balance sheet is over-leveraged.")
                st.write(f"• Total Debt: **${total_debt:,.2f}B**")
                st.write(f"• Cash & Cash Equivalents: **${total_cash:,.2f}B**")
                st.write(f"• Debt-to-Cash Multiplier: **{debt_ratio:.2f}x**")
        except:
            st.error("Missing Balance Sheet Data on Yahoo Finance.")
            debt_pass = False

        try:
            fcf_series = cash_flow.loc['Free Cash Flow'].iloc[0:2].iloc[::-1]
            fcf_years = [d.strftime('%Y') for d in fcf_series.index]
            fcf_vals = [v / 1e9 for v in fcf_series.values]
            fcf_pass = all(v > 0 for v in fcf_vals)

            with st.expander("4. Free Cash Flow (Last 2 Years)", expanded=True):
                if fcf_pass:
                    st.success("✅ **PASS: Cash flow is consistently positive.** Genuine operational liquidity.")
                else:
                    st.error("❌ **FAIL: Negative free cash flow detected.** Company is burning capital.")
                st.write(f"• {fcf_years[0]} Free Cash Flow: **${fcf_vals[0]:,.2f}B**")
                st.write(f"• {fcf_years[1]} Free Cash Flow: **${fcf_vals[1]:,.2f}B**")
        except:
            st.error("Missing Cash Flow Data on Yahoo Finance.")
            fcf_pass = False

        try:
            raw_shares = financials.loc['Diluted Average Shares'].iloc[0]
            share_series = financials.loc['Diluted Average Shares'].iloc[0:3].iloc[::-1]
            share_years = [d.strftime('%Y') for d in share_series.index]
            share_vals = [s / 1e9 for s in share_series.values] 
            shares_pass = (share_vals[2] <= share_vals[1]) and (share_vals[1] <= share_vals[0])
            total_share_change = ((share_vals[2] - share_vals[0]) / share_vals[0]) * 100

            with st.expander("5. Share Count Trend (Last 3 Years)", expanded=True):
                if shares_pass:
                    st.success(f"✅ **PASS: Shares reduced by {abs(total_share_change):.2f}%.** Company is repurchasing stock.")
                else:
                    st.error(f"❌ **FAIL: Shares increased by {total_share_change:+.2f}%.** Shareholder dilution occurring.")
                df_shares = pd.DataFrame({
                    "Fiscal Year": share_years,
                    "Shares Outstanding (Billions)": [f"{s:,.3f}B" for s in share_vals]
                })
                st.table(df_shares)
        except:
            st.error("Missing Share Count Data on Yahoo Finance.")
            shares_pass = False; raw_shares = 1

        st.write("---")
        st.subheader("🎯 Intrinsic Valuation & Price Targets")
        
        try:
            # Bulletproof EPS calculation manually bypassing Yahoo Info
            if raw_shares > 1 and raw_net_income != 0:
                eps = raw_net_income / raw_shares
            else:
                eps = info.get("trailingEps")
                
            if not eps or eps <= 0:
                st.warning("Valid positive EPS data missing, cannot calculate fair value.")
            else:
                growth_rate = min(max((rev_growth_y2 / 100), 0.05), 0.20)
                fair_pe = 15 + (growth_rate * 100 * 0.5) 
                intrinsic_fair_value = eps * fair_pe
                buy_target = intrinsic_fair_value * 0.85
                sell_target = intrinsic_fair_value * 1.30 

                col1, col2, col3 = st.columns(3)
                col1.metric("Buy Entry (15% Discount)", f"${buy_target:,.2f}")
                col2.metric("Estimated Fair Value", f"${intrinsic_fair_value:,.2f}")
                col3.metric("Sell / Trim Target (+30%)", f"${sell_target:,.2f}")

                with st.expander("Show Valuation Math (How this was calculated)", expanded=False):
                    st.markdown(f"""
                    **Step-by-Step Breakdown:**
                    1. **Earnings Per Share (EPS):** ${eps:.2f} *(Calculated as Net Income / Total Shares)*
                    2. **Growth Rate Used:** {growth_rate*100:.2f}% *(Most recent revenue growth, capped between 5% and 20%)*
                    3. **Fair P/E Multiple:** 15 + ({growth_rate*100:.2f} × 0.5) = **{fair_pe:.2f}**
                    4. **Estimated Fair Value:** ${eps:.2f} (EPS) × {fair_pe:.2f} (P/E) = **${intrinsic_fair_value:.2f}**
                    5. **Buy Entry (15% Discount):** ${intrinsic_fair_value:.2f} × 0.85 = **${buy_target:.2f}**
                    6. **Sell Target (30% Premium):** ${intrinsic_fair_value:.2f} × 1.30 = **${sell_target:.2f}**
                    """)

                total_score = sum([rev_pass, margin_pass, debt_pass, fcf_pass, shares_pass])

                if total_score == 5 and current_price <= buy_target:
                    st.success(f"🔥 **ACTION: BUY.** Passed 5/5 fundamental criteria and is trading below the Margin of Safety entry point.")
                elif total_score >= 4 and current_price <= intrinsic_fair_value:
                    st.info(f"👀 **ACTION: ACCUMULATE.** Score: {total_score}/5. Fairly priced relative to cash flows.")
                elif current_price >= sell_target:
                    st.warning(f"⚠️ **ACTION: CONSIDER TRIMMING / SELLING.** Stock is extended >30% past intrinsic fair value.")
                else:
                    st.error(f"🛑 **ACTION: WAIT / PASS.** Company scored {total_score}/5 or the current market price (${current_price:,.2f}) does not offer a margin of safety.")
        except Exception as e:
            st.error("Valuation math failed due to missing financial data.")

    except Exception as e:
        st.error(f"Unable to process full financial dataset for {ticker}. Error details: {e}")
