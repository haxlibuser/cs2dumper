import re
import json
import os
import glob

# Function to convert variable names into a format suitable for C++
def convert_name(name):
    return name.replace("::", "_").replace(" ", "_").replace("-", "_")

# Function to generate the .hpp content (no values ​​defined)
def generate_hpp(structs):
    hpp_content = ""

    for struct_name, variables in structs.items():
        hpp_content += f"inline struct {convert_name(struct_name)}Offsets {{\n"
        for var_name in variables:
            hpp_content += f"\tDWORD {convert_name(var_name)};\n"
        hpp_content += f"}} {convert_name(struct_name)};\n\n"

    return hpp_content

# Function to read offsets and values ​​from the .hpp file
def parse_cpp_offsets(file_path):
    offsets = {}
    current_namespace = None

    # Regular expression to capture the beginning of the namespace
    namespace_pattern = re.compile(r'namespace\s+(\w+)\s*\{')
    # Regular expression to capture variable name and associated value
    offset_pattern = re.compile(r'constexpr\s+std::ptrdiff_t\s+(\w+)\s*=\s*(0x[0-9a-fA-F]+);')

    # Open and read the .hpp file
    with open(file_path, 'r', encoding='utf-8') as cpp_file:
        content = cpp_file.readlines()

        # Process the content line by line
        for line in content:
            # Check if the line contains a namespace definition
            namespace_match = namespace_pattern.search(line)
            if namespace_match:
                current_namespace = namespace_match.group(1)
                if current_namespace not in offsets:
                    offsets[current_namespace] = {}

            # Check if the line contains a variable definition with value
            offset_match = offset_pattern.search(line)
            if offset_match and current_namespace:
                var_name = offset_match.group(1)
                var_value = offset_match.group(2)
                offsets[current_namespace][var_name] = var_value  # Add the actual value of the variable

    # Remove namespaces that do not have variables
    offsets = {ns: vars for ns, vars in offsets.items() if vars}

    return offsets

# Function to save offsets in JSON file
def save_offsets_to_json(offsets, output_file):
    with open(output_file, 'w', encoding='utf-8') as json_file:
        json.dump(offsets, json_file, indent=4)

# Function to generate C++ code to set offsets from JSON in findOffsetByName format
def generate_cpp_offset_code(json_file, output_cpp_file):
    print(f"[DEBUG] Generating C++ code from JSON file: {json_file}")
    with open(json_file, 'r', encoding='utf-8') as f:
        json_data = json.load(f)

    cpp_code = []

    # Loop through namespaces in JSON
    for namespace, offsets in json_data.items():
        cpp_code.append(f"// Assignments for {namespace}")
        cpp_code.append(f"// {namespace} Offsets")

        for var_name in offsets.keys():
            # Generate the line in the requested format
            cpp_code.append(f'{namespace}.{convert_name(var_name)} = findOffsetByName(j, "{namespace}", "{var_name}");')

        cpp_code.append("")  # Adiciona uma linha em branco para separação

    # Grava o código gerado em um arquivo .cpp
    print(f"[DEBUG] Saving the C++ file: {output_cpp_file}")
    with open(output_cpp_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(cpp_code))

# Function to process all .hpp files in a directory
def process_all_cpp_files(directory):
    all_offsets = {}

    # Search for all .hpp files in the folder and subfolders
    cpp_files = glob.glob(os.path.join(directory, '**', '*.hpp'), recursive=True)

    for cpp_file in cpp_files:
        offsets = parse_cpp_offsets(cpp_file)

        # Combine offsets found in all files
        for namespace, namespace_offsets in offsets.items():
            if namespace not in all_offsets:
                all_offsets[namespace] = {}
            all_offsets[namespace].update(namespace_offsets)

    return all_offsets

# Main function
def generate_files(directory):
    # Process all .hpp files
    all_offsets = process_all_cpp_files(directory)

    # Generate the JSON file
    output_json = 'offsets.json'
    save_offsets_to_json(all_offsets, output_json)

    # Generate the HPP file
    output_hpp = 'offsets.hpp'
    with open(output_hpp, 'w', encoding='utf-8') as hpp_file:
        hpp_file.write(generate_hpp(all_offsets))

    # Generate the C++ file for the assignments from the JSON
    output_cpp = 'set_offsets.cpp'
    generate_cpp_offset_code(output_json, output_cpp)

    print(f"Generated files: {output_json}, {output_hpp}, {output_cpp}")

# Run a script
if __name__ == "__main__":
    cpp_directory = 'A2X'  # Path to the folder with the .hpp files
    generate_files(cpp_directory)
