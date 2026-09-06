import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Buffett 5-Check", page_icon="📈")
st.title("5-Metric Value Screener")

ticker = st.text_input("Enter US Ticker:", value="AAPL").upper().strip()

if st.button("Run Screen"):
    try:
        stock = yf.Ticker(ticker)
        financials = stock.financials
        balance_sheet = stock.balance_sheet
        cash_flow = stock.cashflow
        
        # 1. Revenue Growth (Last 3 yrs)
        revs = financials.loc['Total Revenue'].iloc[0:3].iloc[::-1]
        rev_pass = all(revs.iloc[i] > revs.iloc[i-1] for i in range(1, len(revs)))
        
        # 2. Net Margin (>15%)
        margin = (financials.loc['Net Income'].iloc[0] / revs.iloc[-1]) * 100
        margin_pass = margin > 15
        
        # 3. Debt vs Cash (<3x)
        debt = balance_sheet.loc['Total Debt'].iloc[0] if 'Total Debt' in balance_sheet.index else balance_sheet.loc['Long Term Debt'].iloc[0]
        cash = balance_sheet.loc['Cash And Cash Equivalents'].iloc[0]
        debt_pass = debt < (cash * 3)
        
        # 4. Positive FCF (Last 2 yrs)
        fcf = cash_flow.loc['Free Cash Flow'].iloc[0:2]
        fcf_pass = all(fcf > 0)
        
        # 5. Share Count Decreasing
        shares = financials.loc['Diluted Average Shares'].iloc[0:3].iloc[::-1]
        shares_pass = all(shares.iloc[i] < shares.iloc[i-1] for i in range(1, len(shares)))
        
        def badge(passed, text):
            if passed:
                st.success(f"✅ {text}")
            else:
                st.error(f"❌ {text}")

        badge(rev_pass, "Revenue Growth: Last 3 years trending up")
        badge(margin_pass, f"Net Profit Margin: {margin:.1f}% (Target > 15%)")
        badge(debt_pass, f"Debt-to-Cash: Debt is {debt/cash:.1f}x cash (Target < 3x)")
        badge(fcf_pass, "Free Cash Flow: Positive in last 2 years")
        badge(shares_pass, "Share Count: Decreasing (Buybacks)")

    except Exception as e:
        st.warning(f"Couldn't pull all data for {ticker}. Error: {e}")
