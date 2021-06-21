import base64
import glob
import json
import logging
import os
from pathlib import Path
import re
import requests
import shutil
import subprocess
import time
from typing import List, Dict
import urllib.request

import streamlit as st
# import streamlit.components.v1 as stc


def main():
    st.sidebar.markdown("# Streamlit App Maker")

    mode = st.sidebar.selectbox("Main Menu", ["My App", "Component Library"])
    st.sidebar.markdown("-" * 17)

    # Create a placeholder app if no apps have been created yet.)
    if not len(glob.glob(r"app_data/[0-9]*.py")):
        # Add app to ./app_data/app_id.py
        app_id = time.strftime("%Y%m%d-%H%M%S").replace('-', '_')
        Path(f"app_data/").mkdir(parents=True, exist_ok=True)
        my_app_file = f"app_data/{app_id}.py"

        with open(my_app_file, 'w') as f:
            f.write('import streamlit as st\nimport requests\n\n')
            f.write('# Click the `Run App` button in the side panel to test this app\n')
            f.write('st.write("Hello, Streamlit! :sunglasses:")\n')
            f.write('st.video("https://www.youtube.com/watch?v=BkaqYAGwv5g")')

    # Open most reecent app
    else:
        my_app_file = most_recent_app()
        app_id = re.findall(r'\d+.\d+', my_app_file)[0]

    # Navigate to page selected in main menu
    if mode == 'My App':
        my_app(app_id)

    elif mode == 'Component Library':
        component_library(app_id)

    else:
        st.write(':sunglasses:')


def my_app(app_id):
    st.markdown('# My App\n' + '-' * 17)

    # Code editor height in pixels
    HEIGHT = 640

    # Open most recent version of app, or placeholder app if none available.
    my_app_file = f'app_data/{app_id}.py'
    with open(my_app_file, 'r') as f:
        my_app = f.read()

    # Checkbox to show a how to guide for the editor.
    if st.checkbox('How to use'):
        how_to_use_text = """
            The Streamlit App Maker (SAM) facilitates the protoyping of
            Streamlit apps and provides non-technical users with a way to
            implement a quick sketch of their ideas.
            1. Check the `Edit App` box below to edit your app code. Streamlit
            components can be added directly using the `Component Library`
            in the side drop down menu.
            2. When your app is ready to test, click the `Run App` button in the side 
            panel.
            3. Use the `Download App` button in the side panel to download your
            app code for further development or to share."""

        st.markdown(how_to_use_text)

    # Show code in editor formatted for python.
    if st.checkbox('Edit App'):

        # Code editor
        my_app = st.text_area(label="Edit Your App code here",
                              value=my_app,
                              height=HEIGHT)

        # Save the app changes
        try:
            with open(my_app_file, "w") as f:
                f.write(my_app)

        except Exception as e:
            st.error('Failed to save app changes: {}'.format(e))

    else:
        code_display = st.code(my_app, language="python")

    # Button to run the app.
    if st.sidebar.button('Run App'):
        # Stops previous app processes before starting new.
        kill_previous = subprocess.run("ps aux | grep python | grep app_data | grep -E '[0-9]{8}_[0-9]{6}.py' | awk {'print $2'} | xargs kill", shell=True)

        # Run app in subprocess
        run_my_app = subprocess.Popen(f'streamlit run {my_app_file}', shell=True, preexec_fn=os.setsid)

        # Notify user that app is opening in a new window.
        st.sidebar.markdown('Opening app in a new window. Visit http://localhost:8502/ to access app.')

    if st.sidebar.button('Download App'):
        st.sidebar.markdown(download_link(my_app, app_id), unsafe_allow_html=True)


def component_library(app_id):
    st.markdown('# Component Library\n' + '-' * 17)

    # TODO: Update to read from Streamlit API docs
    JSON_URL = "https://raw.githubusercontent.com/virusvn/streamlit-components-demo/master/streamlit_apps.json"
    apps = get_apps(JSON_URL)  # type: Dict[str, str]
    app_names = []

    for name, _ in apps.items():
        app_names.append(name)

    run_app = st.sidebar.selectbox("Select the component", app_names)

    # Fetch the content
    python_code = get_file_content_as_string(apps[run_app])

    # Add component to app
    if st.sidebar.button("Add Component to Your App"):
        # Separate component and imports
        import_re = r'import .+|from .+'
        component_imports = "\n".join(re.findall(import_re, python_code))
        component = re.sub(import_re, r"", python_code).strip()

        # Add component to app
        try:
            # Get filename of current app
            my_app_file = most_recent_app()

            # Append component to current saved app
            with open(my_app_file, "a") as f:
                f.write('\n\n# New Component\n' + component)

            # Open current app for editing
            with open(my_app_file, "r") as f:
                my_app = f.read()

            # Separate app and imports
            my_app_imports = "\n".join(re.findall(import_re, my_app))
            my_app = re.sub(import_re, r"", my_app).strip()

            # Merge component imports and current app imports
            combined_imports = (my_app_imports + '\n' + component_imports).split('\n')
            combined_imports = list(set(combined_imports))
            combined_imports.sort()
            combined_imports = "\n".join(combined_imports)

            # Revised app
            my_app = combined_imports + '\n\n' + my_app

            # Save updated app
            with open(my_app_file, 'w') as f:
                f.write(my_app)

        except Exception as e:
            st.error('Failed to add component: {}'.format(e))

        st.sidebar.markdown('`Success! App Component was added`')

    st.sidebar.markdown('-' * 17)
    st.sidebar.markdown('[Click here to see the Streamlit API docs](https://docs.streamlit.io/en/stable/api.html)')

    # Run the child app
    if python_code:
        try:
            st.header("Result")
            exec(python_code)
            st.header("Source code")
            st.markdown("Link: [Github](%s)" % apps[run_app])
            st.code(python_code)
        except Exception as e:
            st.write("Error occurred when execute [{0}]".format(run_app))
            st.error(str(e))
            logger.error(e)


def download_link(app, app_id):
    """
    Generates a link allowing the given app code to be
    downloaded as a python file.
    app:  string with app code
    app_id: str of the app id
    returns: string with href link to download code
    """
    # some strings <-> bytes conversions necessary here
    b64 = base64.b64encode(app.encode()).decode()
    app_file = f'app_{app_id}.py'

    return f'<a href="data:file/txt;base64,{b64}" download="{app_file}">Click here to download My App code</a>'


def most_recent_app():
    app_list = glob.glob("app_data/[0-9]*.py")
    app_list.sort()
    my_app = app_list[0]
    return my_app


def oldest_n_apps(n):
    app_list = glob.glob(f"app_data/[0-9]*.py")
    app_list.sort(reverse=True)
    my_app = app_list[0:n]
    return my_app


@st.cache(suppress_st_warning=True)
def get_apps(url: str) -> Dict[str, str]:
    json_obj = fetch_json(url)
    apps = {}
    for item in json_obj:
        if item["url"] is not None and item["url"].endswith(".py"):
            # can overwrite if same name
            apps[item["name"]] = item["url"]

    return apps


@st.cache
def fetch_json(url: str):
    data = urllib.request.urlopen(url).read()
    output = json.loads(data)
    return output


@st.cache
def get_file_content_as_string(url: str):
    data = urllib.request.urlopen(url).read()
    return data.decode("utf-8")


if __name__ == "__main__":
    main()