import pandas as pd
import pickle
import json
import geopandas as gpd
import shapefile
import matplotlib.pyplot as plt
import matplotlib
from shapely.geometry import Point
import streamlit as st
from datetime import datetime
import altair as alt
import seaborn as sns

# Import the taxi zoning for identification
taxi_zone = pd.read_csv('./datasets/taxi+_zone_lookup.csv')

# Import the prediciton for all zones
y_22 = pd.read_pickle('./datasets/y_22_preds.pkl')

# Import New York City Geospatial file
geo_df = gpd.read_file("./datasets/taxi_zones/geo_export_457dd3df-f007-4b2c-9373-8ac7fde74fb4.shp") 

# Identify the central coordinate from the geometry shape
geo_df['coords'] = geo_df['geometry'].apply(lambda x: x.representative_point().coords[:])
geo_df['coords'] = [coords[0] for coords in geo_df['coords']]

# To split the coordinate into Longitude and Latitude 
geo_df = pd.concat([geo_df, geo_df['coords'].astype("string").str.split(', ', expand=True)], axis=1)
geo_df.rename(columns = {0:'longitude', 1:'latitude'}, inplace = True)
geo_df['longitude'] = geo_df['longitude'].str.replace('(', '')
geo_df['latitude'] = geo_df['latitude'].str.replace(')', '')

# Data Cleaning on geo_df
geo_df.reset_index(inplace = True)
geo_df.at[56,'zone']='Corona_1'
geo_df.at[104,'zone']="Governor's Island/Ellis Island/Liberty Island_1"
geo_df.at[105,'zone']="Governor's Island/Ellis Island/Liberty Island_2"
geo_df.rename(columns = {"location_i":"LocationID"}, inplace = True)

# Import neighbors dictionary
with open('./datasets/neighbor_weight.txt') as f:
    neighbor = f.read()
neighbors = json.loads(neighbor)

# Title of the page
st.title("🚕🚕 Taxi Driver Go Where?🚕🚕")
st.caption("Driving around aimlessly or Idle waiting are not a good way to know where is your potential passenger customer.")
st.caption("Use this app now to find potential zone with customer demand!")
st.set_option('deprecation.showPyplotGlobalUse', False)

# Get user inputs
option = st.selectbox(
"Where is your current borough?",
(geo_df['borough'].unique()))

borough_list = geo_df['borough'].unique()
borough_zone = {}
for borough in borough_list:
     borough_zone[borough] = geo_df[geo_df['borough'] == borough]['zone'].unique()
        
user_zone = st.selectbox("Where is your current area?",
                             sorted(borough_zone[option]))

# Define empty list to store the followings:
high_demand = []
high_demand_ID = []
demand_30=[]
demand_30_df = pd.DataFrame()

if st.button("Submit Your Borough and Area"): 
    try:   
        # Extract the zone name of the user
        st.write(f"You have selected: {user_zone}")
        
        # To load the neighbors dictionary
        neighbors = json.loads(neighbor)
        
        # Extract the neighboring zones from the user's location
        user_neighbor = list(neighbors[user_zone].keys())
                
        # To incluede the user zone into the list for identifying the demand
        user_neighbor.append(user_zone)
        
        # Extract the current time 
        dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.subheader(f"Current time: {dt}")
        
        st.markdown("""---""")
    
        for area in user_neighbor:
            try:
                # Extract the neighboring zones ID to call from Map data
                zoning = taxi_zone[taxi_zone['Zone'] == area]['LocationID'].values[0]
                               
                # Extract the demand of the neighboring zone based on user's time and 30Mins demand 
                demand_30 = y_22[y_22.index >= dt][zoning]#.values[:6]
                
                demand_30_df = pd.concat([demand_30_df, demand_30[:4]], axis = 1)
                demand_30_df.rename(columns = {zoning:area}, inplace = True)
                                
                # Store the area where demand are positive for the next 30 minuts 
                if all(demand > 0.1 for demand in demand_30.values[:6]):
                    high_demand.append(area)
                    high_demand_ID.append(zoning)

                    
            except:
                pass
        
        

        # If user's current zone is already in high demand
        if user_zone in high_demand:
            st.subheader("Your current area is in demand for taxi!🎉🎉🎉🎉")
            st.write("The taxi demand will stay for the next 1 hour!!")
            

            # To plot map and chart
            chart_data = pd.DataFrame(demand_30_df[user_zone])
            user_geo_df = geo_df[geo_df['zone'] == user_zone]
            
            # Define the coordinate for annotation            
            user_geo_df['coords'] = user_geo_df['geometry'].apply(lambda x: x.representative_point().coords[:])
            user_geo_df['coords'] = [coords[0] for coords in user_geo_df['coords']]


            # Define the plot for map
            fig, ax = plt.subplots(1, 1, figsize = (20,16))

            user_geo_df.plot(column='zone', 
                             cmap = 'Paired', ax=ax)

            # Set the parameters of the map
            ax.set_title(f'You are now at {user_zone}', fontsize = 35)
            ax.set_xlabel('Latitude', fontsize = 30)
            ax.set_ylabel('Latitude', fontsize = 30)
            ax.tick_params(axis='both', which='major', labelsize=25)            
            ax.grid(visible = True)
            for idx, row in user_geo_df.iterrows():
                plt.annotate(text=row['zone'], xy=row['coords'],
                             horizontalalignment='center', fontsize = 20)
            st.pyplot(fig)

            st.line_chart(demand_30_df)
            

        # If user is not located in the high demand zone
        elif len(high_demand) > 0:
            st.subheader("Your neigboring areas with demand are:")
            
            # to list down the zones with high demand
            for town in high_demand:
                st.write(town)
            st.caption("The taxi demand will stay high for the next 1 hour!!")
            
            # Plot a line charts with areas of high demand for next 30 mins
            high_demand.append(user_zone)
            

            # To plot map and chart
            chart_data = pd.DataFrame(demand_30_df[high_demand])
            user_geo_df = geo_df[geo_df['zone'].isin(high_demand)]
            
            # Define the coordinate for annotation            
            user_geo_df['coords'] = user_geo_df['geometry'].apply(lambda x: x.representative_point().coords[:])
            user_geo_df['coords'] = [coords[0] for coords in user_geo_df['coords']]


            # Define the plot for map
            fig, ax = plt.subplots(1, 1, figsize = (20,16))

            user_geo_df.plot(column='zone', 
                             cmap = 'Paired', ax=ax)

            # Set the parameters of the map
            ax.set_title(f'You are now at {user_zone}', fontsize = 35)
            ax.set_xlabel('Latitude', fontsize = 30)
            ax.set_ylabel('Latitude', fontsize = 30)
            ax.tick_params(axis='both', which='major', labelsize=25)            
            ax.grid(visible = True)
            for idx, row in user_geo_df.iterrows():
                plt.annotate(text=row['zone'], xy=row['coords'],
                             horizontalalignment='center', fontsize = 25)
            st.pyplot(fig)

            st.line_chart(demand_30_df)
       
            
            # Define the plot for line chart on demand
            fig, ax2 = plt.subplots(1, 1, figsize = (20,16))
            chart_data.plot(ax = ax2)
            
            ax2.set_title('Demand for Next 30 Mins', fontsize = 35)
            ax2.set_xlabel('Time', fontsize = 30)
            ax2.set_ylabel('Demand', fontsize = 30)
            ax2.set_ylim(0,75)
            ax2.tick_params(axis='both', which='major', labelsize=25)
            ax2.legend(fontsize = 25)
            x2.axhline(0,color="red")
            plt.grid()
            st.pyplot()
                  

        # If the user is located in zone with no demand of taxi    
        else:
            st.subheader("Your current area and nearby areas are not busy 😩")
            st.write("You may explore other nearby area and try again")
        
    except:
        pass

st.markdown("""---""")
