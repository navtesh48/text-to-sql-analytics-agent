"""Streamlit chat + chart + feedback.   run: streamlit run src/sqlagent/app.py"""
import streamlit as st, plotly.express as px
from sqlagent.agent import ask
from sqlagent import feedback

st.title('Algae Farm Analyst')
q = st.chat_input('Ask about ponds, harvests, temperature...')
if q:
    st.session_state['last'] = (q, ask(q))
if 'last' in st.session_state:
    q, r = st.session_state['last']
    st.chat_message('user').write(q)
    with st.chat_message('assistant'):
        st.write(r['answer'])
        if r['sql']:
            with st.expander('SQL'): st.code(r['sql'], language='sql')
        df, ch = r['df'], r['chart']
        if df is not None and not df.empty:
            st.dataframe(df)
            if ch.get('type') in ('bar', 'line', 'scatter') and ch.get('x') in df and ch.get('y') in df:
                st.plotly_chart(getattr(px, ch['type'])(df, x=ch['x'], y=ch['y']))
        c1, c2, _ = st.columns([1, 1, 6])
        if c1.button('Good') and r['sql']: feedback.save_good(q, r['sql']); st.toast('Saved as a verified example')
        if c2.button('Bad') and r['sql']: feedback.save_bad(q, r['sql']); st.toast('Logged')
