import streamlit as st
import pandas as pd
import numpy as np
import re
from copy import copy
import plotly.graph_objs as go
import plotly.express as px

def load(url):
    return pd.read_csv(url)

def preprocess(data):
    data['Amount'] = data['Amount'].apply(lambda x: int(re.sub('[^0-9]', '', x)))
    data['Party'] = data['Party'].map({'Bipartisan': 'Bipartisan',
                 'Bipartisan, but mostly Republican': 'Republican',
                'Bipartisan, but mostly Democratic': 'Democrat',
                'Democrat': 'Democrat',
                'Independent': 'Independent',
                'Republican': 'Republican',
                np.nan: 'Unclassified'})
    data['DonationBin'] = data['Amount'].apply(bin_donation)
    data[['Owner', 'Team', 'Recipient']] = data[['Owner', 'Team', 'Recipient']].apply(lambda x: x.str.title())
    return data

def normalize(data):
    normed = data.copy()
    
    normed = normed.set_index(['Owner', 'Amount', 'Recipient', 'Election Year', 'Party', 'DonationBin'])
    normed['Team'] = normed['Team'].str.split(',')
    normed['League'] = normed['League'].str.split(',')
    
    normed = normed.apply(pd.Series.explode).reset_index()
    normed['Team'] = normed['Team'].str.strip()
    normed['League'] = normed['League'].str.strip()
    
    return normed

def bin_donation(donation):
    if donation < 500:
        return '< $500'
    elif donation < 1000:
        return '$500 to $1k'
    elif donation < 5000:
        return '$1k to $5k'
    elif donation < 10000:
        return '$5k to $10k'
    elif donation < 50000:
        return '$10k to $50k'
    elif donation < 100000:
        return '$50k to $100k'
    elif donation < 500000:
        return '$100k to $500k'
    else:
        return '>= $500k'
    
def filter_main(df, elec_yr, league):
    if (elec_yr == 'All') & (league == 'All'):
        return df
    elif league == 'All':
        return df[df['Election Year']==elec_yr]
    elif elec_yr == 'All':
        return df[df['League']==league]
    else:
        return df[(df['Election Year']==elec_yr)&(df['League']==league)]
    
def filter_table(df, search):
    search = search.title()
    return df[(df['Owner'].str.contains(search, na=False))|(df['Team'].str.contains(search, na=False))|(df['Recipient'].str.contains(search, na=False))]

def make_header_str(base_str, elec_yr, league):
    if league != 'All':
        base_str += f' for {league}'
    if elec_yr != 'All':
        base_str += f' in {elec_yr}'
    return base_str
    
def _max_width_():
    max_width_str = f"max-width: 1000px;"
    st.markdown(
        f"""
    <style>
    .reportview-container .main .block-container{{
        {max_width_str}
    }}
    </style>    
    """,
        unsafe_allow_html=True,
    )
    
def main():
    _max_width_()
    
    SPORTS_DONATIONS_DATA = 'https://raw.githubusercontent.com/fivethirtyeight/data/master/sports-political-donations/sports-political-donations.csv'
    DATA_LINK = 'https://github.com/fivethirtyeight/data/tree/master/sports-political-donations'
    ARTICLE_LINK = 'https://fivethirtyeight.com/features/inside-the-political-donation-history-of-wealthy-sports-owners/'
    
    main_data = load(SPORTS_DONATIONS_DATA)
    main_data = preprocess(main_data)
    by_league = normalize(main_data)
    
    st.sidebar.title('Political Donations of U.S. Sports Owners')
    st.sidebar.markdown(
        'Exploring the data behind FiveThirtyEight\'s [investigation]({ARTICLE_LINK}) '
        'into political donations of U.S. sports franchise owners.\r'
        'Use the dropdowns to filter the data by election year and/or league.\n\n'
        f'''Source Data: [538 Github]({DATA_LINK})'''
    )
    
    elec_yr = st.sidebar.selectbox('Select Election Year', tuple(['All'] + list(np.sort(main_data['Election Year'].unique()))))
    league = st.sidebar.selectbox('Select League', tuple(['All'] + list(by_league['League'].unique())))
    
    if league == 'All':
        data_to_show = filter_main(main_data, elec_yr, league)
    else:
        data_to_show = filter_main(by_league, elec_yr, league)
    
    st.header(make_header_str('Donations Overview', elec_yr, league))
    r1c1, r1c2 = st.beta_columns(2)
    
    r1c1.markdown('<div style="margin-top:50px"></div>', unsafe_allow_html=True)
    r1c1.markdown(f'''<div class="card" style="text-align:center;width: 25rem;background-color:lightblue;;padding: 10px 0; border:10px; border-radius: 25px">
  <div class="card-body">
    <h4 class="card-title" style="font-size:24px">Total Donations</h3>
    <p class="card-text" style="font-size:24px">{len(data_to_show):,d}</p>
  </div>
</div>''', unsafe_allow_html=True)
    r1c1.markdown('<br>', unsafe_allow_html=True)
    
    r1c1.markdown(f'''
    <div class="card" style="text-align: center; width: 25rem;background-color:rgb(255, 0, 0, 0.3);padding: 10px 0; border:10px; border-radius: 25px">
  <div class="card-body">
    <h4 class="card-title" style="font-size:24px">Total Donation Amount</h3>
    <p class="card-text" style="font-size:24px">${data_to_show['Amount'].sum():,.2f}</p>
  </div>
</div>''', unsafe_allow_html=True)
    
    r1c2.markdown('<div style="margin-top:50px"></div>', unsafe_allow_html=True)
    r1c2.markdown(f'''<div class="card" style="text-align:center;width: 25rem;background-color:lightblue;;padding: 10px 0; border:10px; border-radius: 25px">
  <div class="card-body">
    <h4 class="card-title" style="font-size:24px">Median Donation Amount</h3>
    <p class="card-text" style="font-size:24px">${data_to_show['Amount'].median():,.2f}</p>
  </div>
</div>''', unsafe_allow_html=True)
    r1c2.markdown('<br>', unsafe_allow_html=True)
    
    r1c2.markdown(f'''
    <div class="card" style="text-align: center; width: 25rem;background-color:rgb(255, 0, 0, 0.3);padding: 10px 0; border:10px; border-radius: 25px">
  <div class="card-body">
    <h4 class="card-title" style="font-size:24px">Most Frequent Donation Amount</h3>
    <p class="card-text" style="font-size:24px">${data_to_show['Amount'].mode()[0]:,.2f}</p>
  </div>
</div>''', unsafe_allow_html=True)
    
    st.markdown('<div style="margin-top:50px"></div>', unsafe_allow_html=True)
    
    r2c1, r2c2 = st.beta_columns(2)
    
    r2c1.header(make_header_str('Donations By Party', elec_yr, league))
    
    by_party = pd.DataFrame(data_to_show['Party'].value_counts()).reset_index().rename(columns={'index':'Party', 'Party':'Count'})
    
    pie1_fig = px.pie(by_party, values='Count', names='Party', color='Party',
             color_discrete_map={'Democrat':'royalblue',
                                 'Republican':'tomato',
                                 'Bipartisan':'violet',
                                 'Independent':'mediumseagreen', 'Unclassified':'orange'}, height=500, width=500, hole=0.4)
    pie1_fig.update_layout(showlegend=False)
    r2c1.plotly_chart(pie1_fig)
    
    r2c2.header(make_header_str('Donations By Amount', elec_yr, league))
    
    by_donation_bin =  pd.DataFrame(data_to_show['DonationBin'].value_counts()).reset_index().rename(columns={'index': 'Bin', 'DonationBin': 'Count'})
    
    pie2_fig = px.pie(by_donation_bin, values='Count', names='Bin', color='Bin',
             color_discrete_map={'< $500':'yellowgreen',
                                 '$500 to $1k':'orange',
                                 '$1k to $5k':'royalblue',
                                 '$5k to $10k':'tomato',
                                 '$10k to $50k': 'mediumseagreen',
                                 '$50k to $100k': 'violet',
                                 '$100k to $500k':'lightgreen',
                                '>= $500k': 'pink'}, height=500, width=500, hole=0.4)
    pie2_fig.update_layout(showlegend=False)
    r2c2.plotly_chart(pie2_fig)
    
    st.header(make_header_str('Full Donation Data', elec_yr, league))
    free_text = st.text_input('Search by owner, team or recipient:')
    data_to_show_ = filter_table(data_to_show, free_text)
    data_values = [data_to_show_['Owner'],
                   data_to_show_['Team'],
                   data_to_show_['League'],
                   data_to_show_['Recipient'],
                   data_to_show_['Amount'],
                   data_to_show_['Election Year'],
                   data_to_show_['Party']]
    tbl_fig = go.Figure(data=[go.Table(
        header=dict(values=['Owner', 'Team', 'League', 'Recipient', 'Amount', 'Election Year', 'Party'],
                fill_color='paleturquoise',
                align='left'),
        cells=dict(values=data_values,
               fill_color='lavender',
               align='left'))
    ])
    tbl_fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, width=1000)
    st.plotly_chart(tbl_fig)
    
if __name__ == '__main__':
    main()