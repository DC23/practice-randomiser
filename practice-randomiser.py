
# coding: utf-8

# # Music Practice Builder
# - Load data
# - create empty practice session
# - split into essential and non-essential items
# - add essential items to session
# - sort by priority
# 

# ## Configuration

# In[ ]:

import math
import random
import numpy as np
import pandas as pd

get_ipython().magic('matplotlib inline')


# ### Data source

# In[ ]:

#input_file = './practice_elements.xlsx'
input_file = '~/Dropbox/practice_elements.xlsx'


# In[ ]:

session_output_file = './test_session.csv'


# ### Session characteristics

# total_time_minutes is the required total session time, including the task switching padding time.

# In[ ]:

total_time_minutes = 30


# The buffer time provides padding to allow for task switching time. Adjust based on experience with actual time vs session time.

# In[ ]:

buffer_time_per_30_minutes = 5


# In[ ]:

buffer_time = math.ceil(total_time_minutes / 30 * buffer_time_per_30_minutes)
practice_time_minutes = total_time_minutes - buffer_time


# Decide whether the category item count limits are for the entire session, or for each sub-block of time.
# If this value is specified, then the category.max_item values are interpreted as limits per each N-minute block of time, rather than being applied as hard limits on the number of items for the entire session.
# 
# Disable the following variable to interpret the category.max_items values as limits on the entire session.

# In[ ]:

category_item_limits_time_block_minutes = 30


# ### Presets

# In[ ]:

preset = None


# #### In-Depth
# If enabled, this preset scales the item time ranges, allowing generation of sessions with less items and more time per item than the default settings.

# preset = {
#     #'min_min_time': 10,
#     'time_scale': 2,
#     'max_max_time': 10,
#     'min_items': np.nan,  # remove the category min item limits
# }

# ## Load the data

# In[ ]:

categories = pd.read_excel(
    input_file,
    sheetname='categories',
    index_col=0,
    converters=
    {
        'min_items': int,
        'max_items': int,
    })


# In[ ]:

data = pd.read_excel(
    input_file, 
    sheetname='items',
    converters=
    {
        'min_time': int,
        'max_time': int,
        'priority': float,
        'essential': bool,
        'tempo': str,
        'notes': str,
    })


# ### Fill in missing values with sensible defaults

# In[ ]:

data.weight = data.weight.fillna(1)
data.min_time = data.min_time.fillna(2)
data.max_time = data.max_time.fillna(5)
data.sort_order = data.sort_order.fillna(2)
data.tempo = data.tempo.fillna('')
data.notes = data.notes.fillna('')


# ### If required, scale the category max item count limits by the block time

# In[ ]:

if category_item_limits_time_block_minutes:
    category_item_limit_scale = max(1, round(practice_time_minutes / category_item_limits_time_block_minutes))
    categories.min_items *= category_item_limit_scale
    categories.max_items *= category_item_limit_scale


# ### Apply presets

# In[ ]:

if preset:
    def apply_preset(row):
        if not row.essential:
            if 'time_scale' in preset:
                row.min_time = round(row.min_time * preset['time_scale'])
                row.max_time = round(row.max_time * preset['time_scale'])
                
            if 'min_min_time' in preset:
                row.min_time = max(row.min_time, preset['min_min_time'])
    
            if 'max_max_time' in preset:
                row.max_time = min(row.max_time, preset['max_max_time'])
            
            # make sure min_time is less than max_time
            row.min_time = min(row.min_time, row.max_time)  
        return row
    
    data = data.apply(lambda row: apply_preset(row), axis=1)
    
    if 'min_items' in preset:
        categories.loc[:,'min_items'] = preset['min_items']


# ## Generate the random item times

# In[ ]:

def generate_random_times(df):
    return pd.DataFrame(
        {'time': df.apply(lambda row: random.randrange(row.min_time, row.max_time+1), axis=1)}, 
        index=df.index)


# In[ ]:

data = data.join(generate_random_times(data))


# ## Populate the session with the essential items

# In[ ]:

session = data.query('essential == True')


# ## Extract the set of candidate items

# In[ ]:

items = data.query('essential == False and weight > 0')


# ## Process the category minimum item count constraint

# In[ ]:

for category, group in items.groupby('category'):
    # For this category, attempt to select the min number of items
    try:
        min_items = categories.loc[category].min_items
        current = len(session[session.category == category])
        required = min(min_items - current, len(group))
        if not np.isnan(required) and required > 0:
            new_items = group.sample(n=required, weights='weight')
            items = items.drop(new_items.index)
            session = session.append(new_items)
    except:
        pass


# ## Fill the rest of the session

# In[ ]:

while session.time.sum() < practice_time_minutes and len(items) > 0:
    # Clean out any maxed categories from the candidate items
    for category, group in items.groupby('category'):
        current_items_in_category = len(session[session.category == category])
        max_category = categories.loc[category].max_items
        if not np.isnan(max_category) and current_items_in_category >= max_category:
            print('Category "{0}" reached maximum item count ({1})'.format(category, max_category))
            items = items[items.category != category]
        
    # only query candidates where the min time can fit into the remaining time
    remaining_time = practice_time_minutes - session.time.sum()
    candidates = items.query('min_time <= {0}'.format(remaining_time))
    
    # If no candidates left, we must abort
    if len(candidates) == 0:
        print('unable to fill session')
        break
        
    # pick the next item
    i = candidates.sample(n=1, weights='weight')
    
    item_time = i.time.iloc[0]
    item_min_time = i.min_time.iloc[0]
    item_max_time = i.max_time.iloc[0]
        
    if item_time <= remaining_time:
        # if the item fits, use it
        session = session.append(i)
        items = items.drop(i.index)
    else:
        # trim the item time to the remaining (without exceeding item cap)
        print('setting time to remaining')
        i.loc[:,'time'] = min(remaining_time, item_max_time)
        session = session.append(i)
        items = items.drop(i.index)


# ## Final Shuffle
# 
# Shuffle the items within each sort_order group, while still respecting the sort order overall. This prevents essential items always appearing at the start of the session.

# In[ ]:

session['r'] = np.random.uniform(size=len(session))
session.sort_values(by=['sort_order', 'r'], inplace=True)


# # Today's Practice Session

# In[ ]:

session_time = session.time.sum()
print('Planned total time: {0}'.format(total_time_minutes))
print('Estimated total time: {0}'.format(session_time + buffer_time))
print('Session time: {0}'.format(session_time))
print('Planned time buffer: {0}'.format(buffer_time))


# In[ ]:

display_session = session[['name', 'category', 'tempo', 'notes', 'time']]
display_session


# In[ ]:

display_session.to_csv(
    session_output_file,
    index=False,
    index_label=False,
    encoding='utf-8',
)

