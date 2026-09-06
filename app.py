import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Value Screener", page_icon="📈")
st.title("Value Screener & Fair Value")
st.markdown("**Note:** For Canadian stocks, add `.TO` (e.g., `RY.TO`). For US stocks, just type the ticker (e.g., `AAPL`).")

ticker = st.text_input("Enter Ticker:", value="AAPL").upper().strip()

if st.button("Run Screen"):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # 1. Company Identity & Price
        company_name = info.get("longName", ticker)
        current_price = info.get("currentPrice", info.get("previousClose", 0))
        
        st.subheader(f"🏢 {company_name} ({ticker})")
        st.write(f"**Current Price:** ${current_price}")
        
        financials = stock.financials
        balance_sheet = stock.balance_sheet
        cash_flow = stock.cashflow
        
        # Data Extraction 
        try:
            revs = financials.loc['Total Revenue'].iloc[0:3].iloc[::-1]
            rev_pass = all(revs.iloc[i] > revs.iloc[i-1] for i in range(1, len(revs)))
        except: rev_pass = False

        try:
            margin = (financials.loc['Net Income'].iloc[0] / revs.iloc[-1]) * 100
            margin_pass = margin > 15
        except: margin_pass = False; margin = 0

        try:
            debt = balance_sheet.loc['Total Debt'].iloc[0] if 'Total Debt' in balance_sheet.index else balance_sheet.loc['Long Term Debt'].iloc[0]
            cash = balance_sheet.loc['Cash And Cash Equivalents'].iloc[0]
            debt_pass = debt < (cash * 3)
        except: debt_pass = False; debt = 0; cash = 1

        try:
            fcf = cash_flow.loc['Free Cash Flow'].iloc[0:2]
            fcf_pass = all(fcf > 0)
        except: fcf_pass = False

        try:
            shares = financials.loc['Diluted Average Shares'].iloc[0:3].iloc[::-1]
            shares_pass = all(shares.iloc[i] < shares.iloc[i-1] for i in range(1, len(shares)))
        except: shares_pass = False

        # 2. Display Results with Simple Explanations
        st.write("---")
        st.write("### The 5-Point Checklist")
        
        score = sum([rev_pass, margin_pass, debt_pass, fcf_pass, shares_pass])
        
        def display_metric(passed, title, pass_text, fail_text):
            if passed:
                st.success(f"✅ **{title}**: {pass_text}")
            else:
                st.error(f"❌ **{title}**: {fail_text}")

        display_metric(rev_pass, "1. Revenue Growth", 
                       "Revenues are growing consistently over the last 3 years. The business is expanding.", 
                       "Revenues are flat or dropping. The company is losing market share.")
        
        display_metric(margin_pass, f"2. Net Profit Margin ({margin:.1f}%)", 
                       "Over 15%. The company keeps a large chunk of its sales as profit (strong pricing power).", 
                       "Under 15% (or negative). Profit margins are too thin, high costs are eating revenues.")
        
        display_metric(debt_pass, "3. Debt-to-Cash", 
                       "Debt is less than 3x the cash on hand. Financially safe from bankruptcy.", 
                       "Debt is dangerously high compared to cash. High risk in a recession.")
        
        display_metric(fcf_pass, "4. Free Cash Flow", 
                       "Positive for the last 2 years. Generating real, usable cash.", 
                       "Negative. Burning through cash to stay alive.")
        
        display_metric(shares_pass, "5. Share Count", 
                       "Buying back shares. Your slice of the pie is getting bigger for free.", 
                       "Issuing new shares (diluting). Your ownership percentage is shrinking.")

        # 3. Fair Value & Final Recommendation
        st.write("---")
        st.write("### Valuation & Recommendation")
        
        eps = info.get("trailingEps", 0)
        bvps = info.get("bookValue", 0)
        
        fair_value = 0
        if eps and bvps and eps > 0 and bvps > 0:
            fair_value = (22.5 * eps * bvps) ** 0.5
            st.info(f"⚖️ **Estimated Fair Value (Graham Number):** ${fair_value:.2f}")
            
            if current_price < fair_value:
                st.success("🏷️ **Price Check:** The stock is currently trading BELOW its Fair Value (Discount).")
            else:
                st.warning("🎈 **Price Check:** The stock is currently trading ABOVE its Fair Value (Premium).")
        else:
            st.info("⚖️ **Estimated Fair Value:** Cannot calculate (Earnings or Book Value is negative/missing).")

        # Final Verdict Logic
        if score == 5 and (fair_value > current_price):
            st.success("🎯 **FINAL VERDICT: STRONG BUY CONSIDERATION.** Passes all fundamental checks and is currently undervalued.")
        elif score >= 4:
            st.warning(f"🤔 **FINAL VERDICT: WATCHLIST ({score}/5).** Good company, but failed a check or is too expensive right now. Investigate further.")
        else:
            st.error(f"🛑 **FINAL VERDICT: AVOID ({score}/5).** The financials are too weak based on this criteria.")

    except Exception as e:
        st.error(f"Error pulling data. Check if the ticker is correct. Details: {e}")
