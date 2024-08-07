import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from sklearn.preprocessing import MinMaxScaler
from pandas.plotting import parallel_coordinates
import pandas as pd
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import itertools

def load_and_normalize_file(file_path):
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    elif file_path.endswith('.txt'):
        df = pd.read_csv(file_path, delimiter='\t')
    else:
        messagebox.showerror("Error", "Unsupported file type. Please select a CSV or TXT file.")
        return None, None, None, None, None, None
    
    if 'class' not in df.columns:
        messagebox.showerror("Error", "The selected file does not contain a 'class' column.")
        return None, None, None, None, None, None

    labels = df['class']
    data = df.drop(columns=['class']).values
    scaler = MinMaxScaler()
    normalized_data = scaler.fit_transform(data)
    feature_names = list(df.columns.drop('class'))
    class_names = sorted(labels.unique().astype(str).tolist())
    label_to_index = {class_name: index for index, class_name in enumerate(class_names)}
    labels = labels.map(label_to_index)
    return normalized_data, labels, feature_names, scaler, class_names, df

def calculate_label_positions(num_features, radius):
    positions = []
    for i in range(num_features):
        angle = 2 * np.pi * i / num_features - np.pi / 2  # Start from the top and move clockwise
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        positions.append((x, y))
    return positions

def plot_circular_coordinates(data, labels, feature_names, scaler, class_order, feature_order, ax, highlighted_index=None):
    ax.clear()
    feature_order = np.roll(feature_order, len(feature_order) // 2)
    feature_order = feature_order[::-1]
    feature_order = np.roll(feature_order, 1)
    
    num_classes = len(np.unique(labels))
    num_features = data.shape[1]
    
    angles = np.linspace(2 * np.pi, 0, num_features + 1, endpoint=True)
    radii = np.linspace(1, num_classes, num_classes)
    
    for radius in radii:
        circle = plt.Circle((0, 0), radius, color='black', fill=False, linestyle='dashed')
        ax.add_artist(circle)
        for angle in angles:
            x, y = -radius * np.sin(angle), radius * -np.cos(angle)
            ax.plot([0, x], [0, y], color='black', linestyle='dashed', linewidth=0.5)
    
    label_positions = calculate_label_positions(num_features, radii[-1] * 1.4)

    for i, feature_idx in enumerate(feature_order):
        adjusted_index = i
        sector_start = angles[adjusted_index]
        sector_end = angles[adjusted_index + 1]
        
        original_min = scaler.data_min_[feature_idx]
        original_max = scaler.data_max_[feature_idx]
        normalized_range = f"[{0:.2f} - {1:.2f}]"
        original_range = f"[{original_min:.2f} - {original_max:.2f}]"
        
        x, y = label_positions[adjusted_index]
        
        ax.text(x, y, f"{feature_names[feature_idx]}\nNorm: {normalized_range}\nOrig: {original_range}", 
                ha='center', va='center', fontsize=8, bbox=dict(facecolor='white', alpha=0.5))

    scatter_plots = []
    for j in range(len(data)):
        class_label = labels[j]
        radius = radii[class_order.index(class_label)]
        for i, feature_idx in enumerate(feature_order):
            adjusted_index = i
            sector_start = angles[adjusted_index + 1]
            sector_end = angles[adjusted_index]
            data_angle = np.interp(data[j, feature_idx], [0, 1], [sector_start, sector_end])
            x, y = radius * -np.cos(data_angle), radius * np.sin(data_angle)
            if highlighted_index is not None and j == highlighted_index:
                # connect the highlighted scatter points with a polyline
                x_max, y_max = radii[-1] * -np.cos(data_angle), radii[-1] * np.sin(data_angle)
                ax.plot([0, x_max], [0, y_max], color='yellow', linestyle='-', linewidth=2, zorder=0)
                ax.scatter(x, y, color=[1, 0, 0], alpha=1, s=135, edgecolors='black', linewidth=1)
                ax.scatter(x, y, color=[1, 1, 0], alpha=0.75, s=125)
                
            scatter = ax.scatter(x, y, color=class_colors[class_label], alpha=0.3 if j != highlighted_index else 1, picker=True)
            scatter_plots.append((scatter, j))
    
    ax.set_aspect('equal', adjustable='box')
    ax.set_xticks([])
    ax.set_yticks([])
    return scatter_plots

def plot_parallel_coordinates(data, labels, feature_names, class_order, feature_order, ax2, highlighted_index=None):
    ax2.clear()

    df = pd.DataFrame(data, columns=feature_names)
    df['Class'] = labels
    
    reordered_columns = [feature_names[i] for i in feature_order] + ['Class']
    df = df[reordered_columns]
    
    # Map labels to colors using class_colors
    label_color_map = {label: class_colors[label] for label in df['Class'].unique()}
    
    for class_label, color in label_color_map.items():
        subset = df[df['Class'] == class_label]
        parallel_coordinates(subset, 'Class', color=[color], ax=ax2, linewidth=1, alpha=0.33)
    
    if highlighted_index is not None:
        df_highlighted = df.iloc[[highlighted_index]]
        parallel_coordinates(df_highlighted, 'Class', color=[1, 1, 0], ax=ax2, linewidth=2.5)

    ax2.set_xticklabels([feature_names[i] for i in feature_order], rotation=30, ha='right')
    ax2.legend().set_visible(False)

def plot_table(df, table):
    for col in table.get_children():
        table.delete(col)
    
    table["show"] = "headings"
    
    table["columns"] = list(df.columns)

    for col in table["columns"]:
        table.heading(col, text=col)
        table.column(col, width=20, anchor='center')
    
    for i, row in df.iterrows():
        values = [row[col] for col in table["columns"]]
        table.insert("", "end", values=values)

def highlight_row(table, index):
    for row in table.get_children():
        table.item(row, tags=())

    if index is not None:
        item_id = table.get_children()[index]
        table.item(item_id, tags=('highlight',))
        table.tag_configure('highlight', background='yellow')
        table.see(item_id)

def update_plot(highlighted_index=None):
    selected_class_order = class_order_combobox.get()
    selected_feature_order = feature_order_combobox.get()
    class_order = [class_names.index(c.strip()) for c in selected_class_order.split(',')]
    feature_order = [feature_names.index(f.strip()) for f in selected_feature_order.split(',')]
    global scatter_plots
    scatter_plots = plot_circular_coordinates(data, labels, feature_names, scaler, class_order, feature_order, ax, highlighted_index)
    plot_parallel_coordinates(data, labels, feature_names, class_order, feature_order, ax2, highlighted_index)
    plot_table(original_df, table)
    highlight_row(table, highlighted_index)
    update_legend()
    canvas.draw()

def get_class_colors(labels):
    unique_labels = np.unique(labels)
    class_colors = {label: mcolors.hsv_to_rgb((i / len(unique_labels), 1, 1)) for i, label in enumerate(unique_labels)}
    for label in unique_labels:
        class_name = class_names[label]
        if class_name.lower() == 'benign':
            class_colors[label] = 'green'
        elif class_name.lower() == 'malignant':
            class_colors[label] = 'red'
    return class_colors

def load_file():
    file_path = filedialog.askopenfilename(initialdir='datasets', filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt")])
    if file_path:
        result = load_and_normalize_file(file_path)
        if result[0] is not None:
            global data, labels, feature_names, scaler, class_names, original_df, class_colors
            data, labels, feature_names, scaler, class_names, original_df = result
            class_colors = get_class_colors(labels)  # Initialize class_colors here
            update_controls()
            update_plot()

def update_controls():
    class_permutations = [','.join(p) for p in itertools.permutations(class_names)]
    class_order_combobox['values'] = class_permutations
    class_order_combobox.set(class_permutations[0])  # Default class order
    
    feature_permutations = [','.join(p) for p in itertools.permutations(feature_names)]
    feature_order_combobox['values'] = feature_permutations
    feature_order_combobox.set(feature_permutations[0])  # Default feature order

def update_legend():
    if fig.legends:
        fig.legends.clear()
    legend_handles = []
    
    class_counts = labels.value_counts().to_dict()
    for label, color in class_colors.items():
        class_name = class_names[label]
        count = class_counts.get(label, 0)
        legend_handles.append(plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=color, markersize=10, label=f"{class_name} ({count})"))
    
    fig.legend(handles=legend_handles, loc='upper center', bbox_to_anchor=(0.5, 0.965), ncol=len(class_names), title="Classes")

# Center the window on open
def center_window(root):
    root.update_idletasks()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight() - 65
    window_width = root.winfo_width()
    window_height = root.winfo_height()
    position_right = int(screen_width / 2 - window_width / 2)
    position_down = int(screen_height / 2 - window_height / 2)
    root.geometry(f"+{position_right}+{position_down}")

# Initialize global variables
data, labels, feature_names, scaler, class_names, original_df = None, None, None, None, None, None

root = tk.Tk()
root.title("Scatterplot Control Panel")
root.geometry("1900x1000")

# Center the window
center_window(root)

# Main frame to hold plot and controls
mainframe = ttk.Frame(root, padding="10 10 10 10")
mainframe.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

# Plot frame
plot_frame = ttk.Frame(mainframe, padding="10 10 10 10")
plot_frame.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

fig, (ax, ax2) = plt.subplots(1, 2, figsize=(18, 6), gridspec_kw={'width_ratios': [1, 1.5], 'wspace': 0.75})
fig.suptitle("SCC Scatterplot Multi-Axes vs Parallel Coordinates", y=0.98, x=0.5)
canvas = FigureCanvasTkAgg(fig, master=plot_frame)
canvas.get_tk_widget().grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

# Scrollable table frame
table_frame = ttk.Frame(mainframe, padding="10 10 10 10")
table_frame.grid(column=0, row=1, sticky=(tk.W, tk.E, tk.N, tk.S))

# Create the table and add scrollbars to it
table = ttk.Treeview(table_frame, show="headings", selectmode="browse")
v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
v_scrollbar.pack(side="right", fill="y")
h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=table.xview)
h_scrollbar.pack(side="bottom", fill="x")
table.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
table.pack(side="left", fill="both", expand=True)

# Frame for controls
control_frame = ttk.Frame(mainframe, padding="0 0 0 0")
control_frame.grid(column=0, row=2, sticky=(tk.W, tk.E))

# Class order combobox
ttk.Label(control_frame, text="Class Order").grid(column=0, row=0, sticky=tk.W)
class_order_combobox = ttk.Combobox(control_frame, width=40)
class_order_combobox.grid(column=1, row=0, sticky=(tk.W, tk.E))

# Feature order combobox
ttk.Label(control_frame, text="Feature Order").grid(column=0, row=1, sticky=tk.W)
feature_order_combobox = ttk.Combobox(control_frame, width=40)
feature_order_combobox.grid(column=1, row=1, sticky=(tk.W, tk.E))

# Update plot button
ttk.Button(control_frame, text="Update Plot", command=lambda: update_plot(None)).grid(column=1, row=2, sticky=tk.E)

# Load file button
ttk.Button(control_frame, text="Load File", command=load_file).grid(column=0, row=2, sticky=tk.W)

# Adjust grid configurations for resizing
mainframe.columnconfigure(0, weight=1)
mainframe.rowconfigure(0, weight=1)
mainframe.rowconfigure(1, weight=0)

plot_frame.columnconfigure(0, weight=1)
plot_frame.rowconfigure(0, weight=1)

control_frame.columnconfigure(1, weight=1)

# Event handling for highlighting
def onpick(event):
    scatter = event.artist
    for sp, ind in scatter_plots:
        if sp == scatter:
            update_plot(ind)
            break

canvas.mpl_connect('pick_event', onpick)

# Table row click event
def on_row_click(event):
    selected_item = table.selection()
    if selected_item:
        index = table.index(selected_item[0])
        update_plot(index)

table.bind('<<TreeviewSelect>>', on_row_click)

root.mainloop()
