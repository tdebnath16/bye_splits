#data = 

'''# Now df_tcell_layers contains the DataFrame that was saved in the file
print(df_tcell_layers.head())  # Display the first few rows of the DataFrame
# Now you can work with the data as a pandas DataFrame'''
# Plotting the histogram of seed energy
plt.hist(df['Seed_Energy'], bins=30, alpha=0.7, color='blue', edgecolor='black')
plt.title('Histogram of Cluster Energy')
plt.xlabel('Energy')
plt.ylabel('Frequency')
plt.savefig('Histogram_Cluster_Energy.png')
plt.show()
'''data.hist(column='pt', bins=30)  # You can adjust the number of bins as needed

plt.xlabel('pT')
plt.ylabel('Frequency')
plt.title('Histogram of pT')

# Save the plot
plt.savefig('pT_histogram.png')

print(data.head())  # Display the first few rows of the DataFrame
plt.scatter(data['pt'], data.index)
plt.ylabel('Seed Index')
plt.xlabel('Cluster p_T')
plt.title('Seed Index vs Cluster pT')
plt.savefig('seed_idx_vs_cluster_pT.png')
plt.show()
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# Plotting
ax.scatter(data['x'], data['y'], data['z'])

ax.set_xlabel('X Coordinate')
ax.set_ylabel('Y Coordinate')
ax.set_zlabel('Z Coordinate')
plt.title('3D Scatter Plot of Clusters')

# Show the plot
plt.show()

# Save the plot, if needed
plt.savefig('3D_scatter_plot.png')'''
