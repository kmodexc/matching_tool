def switch_names(df, assigned_names, not_assigned_names):
    # Ensure the same number of names in both lists
    if len(assigned_names) != len(not_assigned_names):
        raise ValueError("The number of assigned and not assigned names must be the same to swap.")

    # Create a mapping of names to their corresponding row indices
    name_to_index = {name: idx for idx, name in enumerate(df['name'])}

    # Get the indices for assigned and not assigned names
    assigned_indices = [name_to_index[name] for name in assigned_names]
    not_assigned_indices = [name_to_index[name] for name in not_assigned_names]

    # Swap the rows in the DataFrame
    temp = df.loc[assigned_indices].copy()
    df.loc[assigned_indices] = df.loc[not_assigned_indices].values
    df.loc[not_assigned_indices] = temp.values

    return df
import pandas as pd

# Sample DataFrame
data = {'name': ['Alice', 'Bob', 'Charlie', 'David'],
        'n_shifts': [1, 2, 3, 4]}
df = pd.DataFrame(data)

# Assigned and Not Assigned Names
assigned_names = ['Alice', 'Charlie']
not_assigned_names = ['Bob', 'David']

# Perform the swap
df = switch_names(df, assigned_names, not_assigned_names)
print(df)
