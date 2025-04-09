import streamlit as st

# We decide to use a stack to track page history. Use stack methods.
def go_to_page(page_name: str):
    st.session_state['page_stack'].append(page_name)
    st.session_state['page'] = page_name
    st.rerun()

def go_back():
    if not len(st.session_state['page_stack']):
        # Hacky method: if somehow the page isn't initialized properly, make it so it goes
        # back to login twice
        st.session_state['page_stack'] = ['Login', 'Login']

    prev_page = st.session_state['page_stack'].pop()
    st.session_state['page'] = prev_page