def calculate_area(length, width, height=1):
    return length * width * height



def calculate_sheets_needed(total_area, sheet_area=32):
    return total_area / sheet_area

def calculate_material_cost(material_type, quantity, material_costs):
    if material_type in material_costs:
        return material_costs[material_type] * quantity
    else:
        raise ValueError("Material type not found in cost table.")

def total_cost(material_costs, selections):
    total = 0
    for material_type, quantity in selections.items():
        total += calculate_material_cost(material_type, quantity, material_costs)
    return total

def calculate_total_area(elements):
    total_area = 0
    for element in elements:
        total_area += calculate_area(element['length'], element['width'], element['height'])
    return total_area

def shutter_area(height, length):
    """Calculate Shutter Area = Height * Length"""
    return height * length

def side_area(width, height):
    """Calculate Side Area = 2 * Width * Height"""
    return 2 * width * height

def top_bottom_area(length, width):
    """Calculate Top & Bottom Area = 2 * Length * Width"""
    return 2 * length * width

def back_panel_area(height, length):
    """Calculate Back Panel Area = Height * Length"""
    return height * length

def shelf_area(num_shelves, width, length, height=1):
    """Calculate Shelf Area = No. of Shelves * Width * Length * Height"""
    return num_shelves * width * length * height


def calculate_total_element_area(length, width, height, num_shelves=0):
    """
    Calculate total area for an element as the sum of:
    Shutter Area, Side Area, Top & Bottom Area, Back Panel Area, Shelf Area
    """
    shutter = shutter_area(height, length)
    side = side_area(width, height)
    top_bottom = top_bottom_area(length, width)
    back_panel = back_panel_area(height, length)
    shelf = shelf_area(num_shelves, width, length)
    return shutter + side + top_bottom + back_panel + shelf
