# Interior Cost Calculator

This project is a Streamlit application designed to help users calculate the interior costs based on various parameters such as house type, number of bedrooms, room types, and selected elements. 

## Features

- Select house type (Apartment flat, Independent House, Villa)
- Specify the number of bedrooms
- Choose room types (Master, Child, Guest, Other)
- Input dimensions and specifications for various elements (e.g., Wardrobe, Loft, TV Unit)
- Calculate total area for each element
- Determine the number of sheets of 8x4 required
- Select material types for Shutters, Carcus, and Laminate based on a material cost table

## Project Structure

```
interior-cost-calculator
├── src
│   ├── app.py                # Main entry point of the Streamlit application
│   ├── components
│   │   ├── __init__.py       # Empty initializer for components package
│   │   └── ui_elements.py     # UI elements for the Streamlit app
│   ├── data
│   │   └── material_costs.py  # Material cost table
│   └── utils
│       └── calculations.py     # Utility functions for calculations
├── requirements.txt           # Project dependencies
└── README.md                  # Project documentation
```

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd interior-cost-calculator
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the Streamlit application:
   ```
   streamlit run src/app.py
   ```

## Usage Guidelines

- Upon running the application, users will be prompted to select their house type and input the number of bedrooms.
- Users can then specify the room types and dimensions for each element they wish to include in their interior design.
- The application will calculate the total area and provide the necessary material requirements based on user inputs.

## License

This project is licensed under the MIT License.