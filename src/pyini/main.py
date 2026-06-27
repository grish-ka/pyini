import curses
import configparser
import os
import glob

# --- 1. GLOBAL UI SETTINGS ---
def setup_colors():
    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)   # Main Background
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Dialog Box
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLUE)   # Highlight
    curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_WHITE)   # Box Title
    curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_BLACK)  # Drop Shadow

def draw_shadow(stdscr, start_y, start_x, box_height, box_width):
    screen_height, screen_width = stdscr.getmaxyx()
    stdscr.attron(curses.color_pair(5))
    for i in range(box_height):
        if start_y + i + 1 < screen_height and start_x + 2 + box_width <= screen_width:
            stdscr.addstr(start_y + i + 1, start_x + 2, " " * box_width)
    stdscr.attroff(curses.color_pair(5))
    stdscr.refresh()


# --- 2. FILE PICKER MENU ---
def find_inis_menu(stdscr):
    """Scans the current directory for .ini files and lets the user pick one."""
    current_row = 0
    
    while True:
        ini_files = glob.glob("*.ini")
        if not ini_files:
            return "config.ini" # Fallback if none exist
            
        stdscr.clear()
        stdscr.bkgd(' ', curses.color_pair(1))
        
        screen_height, screen_width = stdscr.getmaxyx()
        box_height, box_width = 18, 74
        start_y = (screen_height // 2) - (box_height // 2)
        start_x = (screen_width // 2) - (box_width // 2)

        draw_shadow(stdscr, start_y, start_x, box_height, box_width)

        win = curses.newwin(box_height, box_width, start_y, start_x)
        win.bkgd(' ', curses.color_pair(2))
        win.box() 
        
        title = " Select Configuration File "
        win.addstr(0, (box_width // 2) - (len(title) // 2), title, curses.color_pair(4) | curses.A_BOLD)
        win.addstr(2, 2, "Found these .ini files in the current directory:")

        for idx, file in enumerate(ini_files):
            if idx > 10: break 
            x, y = 5, 5 + idx
            
            if idx == current_row:
                win.attron(curses.color_pair(3) | curses.A_BOLD)
                win.addstr(y, x, f" [*] {file} ".ljust(60))
                win.attroff(curses.color_pair(3) | curses.A_BOLD)
            else:
                win.addstr(y, x, f" [ ] {file} ")

        win.refresh()

        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(ini_files) - 1:
            current_row += 1
        elif key == curses.KEY_ENTER or key in [10, 13]: 
            return ini_files[current_row] 
        elif key == ord('q'):
            return None


# --- 3. POPUP DIALOGS ---
def edit_value_popup(stdscr, key_name, current_value):
    """Creates a small pop-up box to type a new value."""
    h, w = 7, 50
    sh, sw = stdscr.getmaxyx()
    y, x = (sh // 2) - (h // 2), (sw // 2) - (w // 2)

    draw_shadow(stdscr, y, x, h, w)

    win = curses.newwin(h, w, y, x)
    win.bkgd(' ', curses.color_pair(2))
    win.box()
    
    win.addstr(0, (w // 2) - 6, " Edit Value ", curses.color_pair(4) | curses.A_BOLD)
    win.addstr(2, 2, f"Key: {key_name}")
    win.addstr(3, 2, f"Current: {current_value}")
    win.addstr(4, 2, "New: ")
    win.refresh()

    curses.curs_set(1)
    curses.echo()
    curses.cbreak()
    
    new_value_bytes = win.getstr(4, 7, 35) 
    new_value = new_value_bytes.decode('utf-8').strip()
    
    curses.noecho()
    curses.curs_set(0)

    return new_value if new_value else current_value

def add_section_popup(stdscr):
    """Creates a small pop-up box to type a new section name."""
    h, w = 6, 50
    sh, sw = stdscr.getmaxyx()
    y, x = (sh // 2) - (h // 2), (sw // 2) - (w // 2)

    draw_shadow(stdscr, y, x, h, w)

    win = curses.newwin(h, w, y, x)
    win.bkgd(' ', curses.color_pair(2))
    win.box()
    
    win.addstr(0, (w // 2) - 7, " Add Section ", curses.color_pair(4) | curses.A_BOLD)
    win.addstr(2, 2, "New Section Name (use dots for subsections): ")
    win.refresh()

    curses.curs_set(1)
    curses.echo()
    curses.cbreak()
    
    new_name_bytes = win.getstr(2, 2, 40) # Adjusted position for longer prompt
    new_name = new_name_bytes.decode('utf-8').strip()
    
    curses.noecho()
    curses.curs_set(0)

    return new_name

def add_key_popup(stdscr):
    """Creates a small pop-up box to type a new key name."""
    h, w = 6, 50
    sh, sw = stdscr.getmaxyx()
    y, x = (sh // 2) - (h // 2), (sw // 2) - (w // 2)

    draw_shadow(stdscr, y, x, h, w)

    win = curses.newwin(h, w, y, x)
    win.bkgd(' ', curses.color_pair(2))
    win.box()
    
    win.addstr(0, (w // 2) - 5, " Add Key ", curses.color_pair(4) | curses.A_BOLD)
    win.addstr(2, 2, "New Key Name: ")
    win.refresh()

    curses.curs_set(1)
    curses.echo()
    curses.cbreak()
    
    new_name_bytes = win.getstr(2, 16, 25) 
    new_name = new_name_bytes.decode('utf-8').strip()
    
    curses.noecho()
    curses.curs_set(0)

    return new_name


# --- 4. SUBMENU (KEYS & VALUES) ---
def handle_submenu(stdscr, section_name, config):
    current_row = 0

    while True:
        stdscr.clear()
        stdscr.bkgd(' ', curses.color_pair(1))
        
        items = list(config[section_name].items())
        
        screen_height, screen_width = stdscr.getmaxyx()
        box_height, box_width = 18, 74
        start_y = (screen_height // 2) - (box_height // 2)
        start_x = (screen_width // 2) - (box_width // 2)

        draw_shadow(stdscr, start_y, start_x, box_height, box_width)

        win = curses.newwin(box_height, box_width, start_y, start_x)
        win.bkgd(' ', curses.color_pair(2))
        win.box() 
        
        title = f" Editing: [{section_name}] "
        win.addstr(0, (box_width // 2) - (len(title) // 2), title, curses.color_pair(4) | curses.A_BOLD)
        
        win.addstr(1, 2, "Hotkeys: [a] Add Key  [d] Delete Key  [Enter] Edit")
        win.addstr(2, 2, "Press 'Esc' or 'q' to return to main menu.")

        inner_w = box_width - 6
        win.addstr(4, 3, "+" + "-" * (inner_w - 2) + "+")
        win.addstr(13, 3, "+" + "-" * (inner_w - 2) + "+")
        for i in range(5, 13):
            win.addstr(i, 3, "|")
            win.addstr(i, box_width - 4, "|")

        if not items:
            win.addstr(6, 6, "  (Empty - Press 'a' to add a key)  ")
        else:
            for idx, (key, value) in enumerate(items):
                if idx > 7: break 
                x, y = 5, 5 + idx
                
                text_part = f"  {key.ljust(16)} = {value}"
                padding = (inner_w - 6) - len(text_part)
                
                if padding < 0:
                    text_part = text_part[:(inner_w - 9)] + "..."
                    padding = 0
                    
                display_text = text_part + (" " * padding)
                
                if idx == current_row:
                    win.attron(curses.color_pair(3) | curses.A_BOLD)
                    win.addstr(y, x, display_text)
                    win.attroff(curses.color_pair(3) | curses.A_BOLD)
                else:
                    win.addstr(y, x, display_text)

        button_y = box_height - 2
        win.addstr(button_y, (box_width // 2) - 18, "< Edit >", curses.color_pair(3) | curses.A_BOLD)
        win.addstr(button_y, (box_width // 2) - 4, "< Back >")
        win.addstr(button_y, (box_width // 2) + 8, "< Help >")

        win.refresh()

        ch = stdscr.getch()
        if ch == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif ch == curses.KEY_DOWN and current_row < len(items) - 1:
            current_row += 1
        elif ch == ord('q') or ch == 27: 
            break 
            
        elif ch == ord('d'):
            if items:
                selected_key = items[current_row][0]
                config.remove_option(section_name, selected_key)
                current_row = max(0, current_row - 1) 
                
        elif ch == ord('a'):
            new_key = add_key_popup(stdscr)
            if new_key and not config.has_option(section_name, new_key):
                new_val = edit_value_popup(stdscr, new_key, "")
                config.set(section_name, new_key, new_val)
                current_row = len(config[section_name]) - 1
                
        elif ch == curses.KEY_ENTER or ch in [10, 13]:
            if items:
                selected_key, current_val = items[current_row]
                new_val = edit_value_popup(stdscr, selected_key, current_val)
                config.set(section_name, selected_key, new_val)


# --- 5. MAIN MENU ---
def draw_menu(stdscr, selected_row_idx, sections):
    stdscr.bkgd(' ', curses.color_pair(1))
    stdscr.clear()
    
    stdscr.addstr(1, 2, " py-iniview v1.0 - Terminal IDE ", curses.A_BOLD)

    screen_height, screen_width = stdscr.getmaxyx()
    box_height, box_width = 18, 74
    start_y = (screen_height // 2) - (box_height // 2)
    start_x = (screen_width // 2) - (box_width // 2)

    draw_shadow(stdscr, start_y, start_x, box_height, box_width)

    win = curses.newwin(box_height, box_width, start_y, start_x)
    win.bkgd(' ', curses.color_pair(2))
    win.clear()
    win.box() 
    
    title = " Configuration Sections "
    win.addstr(0, (box_width // 2) - (len(title) // 2), title, curses.color_pair(4) | curses.A_BOLD)
    
    inner_w = box_width - 6
    win.addstr(4, 3, "+" + "-" * (inner_w - 2) + "+")
    win.addstr(13, 3, "+" + "-" * (inner_w - 2) + "+")
    for i in range(5, 13):
        win.addstr(i, 3, "|")
        win.addstr(i, box_width - 4, "|")

    for idx, section in enumerate(sections):
        if idx > 7: break 
        x, y = 5, 5 + idx
        
        text_part = f"  {section} "
        padding = (inner_w - 6) - len(text_part)
        display_text = text_part + (" " * padding) + "--->"
        
        if idx == selected_row_idx:
            win.attron(curses.color_pair(3) | curses.A_BOLD)
            win.addstr(y, x, display_text)
            win.attroff(curses.color_pair(3) | curses.A_BOLD)
        else:
            win.addstr(y, x, display_text)

    button_y = box_height - 2
    win.addstr(button_y, (box_width // 2) - 18, "<Select>", curses.color_pair(3) | curses.A_BOLD)
    win.addstr(button_y, (box_width // 2) - 4, "< Save >")
    win.addstr(button_y, (box_width // 2) + 8, "< Exit >")

    win.refresh()

# --- 6. CORE LOOP ---
def main(stdscr):
    setup_colors()
    curses.curs_set(0)

    # Launch File Picker
    config_file = find_inis_menu(stdscr)
    if not config_file:
        return 
        
    config = configparser.ConfigParser()
    
    if os.path.exists(config_file):
        config.read(config_file)
    else:
        config.read_dict({'New_Section': {'key': 'value'}})
    
    current_row = 0

    while True:
        sections = config.sections()
        if not sections:
            sections = ["(Empty - Press 'a' to add a section)"]

        draw_menu(stdscr, current_row, sections)
        
        stdscr.addstr(2, 2, "Hotkeys: [a] Add Section  [d] Delete Section  [s] Save  [q] Quit", curses.color_pair(1) | curses.A_BOLD)
        stdscr.refresh()

        key = stdscr.getch()

        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(sections) - 1:
            current_row += 1
        elif key == curses.KEY_ENTER or key in [10, 13]: 
            if sections[0] != "(Empty - Press 'a' to add a section)":
                handle_submenu(stdscr, sections[current_row], config)
        elif key == ord('d'):
            if sections[0] != "(Empty - Press 'a' to add a section)":
                config.remove_section(sections[current_row])
                current_row = max(0, current_row - 1)
        elif key == ord('a'):
            new_section = add_section_popup(stdscr)
            if new_section and not config.has_section(new_section):
                config.add_section(new_section)
                current_row = len(config.sections()) - 1 
        elif key == ord('s'):
            with open(config_file, 'w') as configfile:
                config.write(configfile)
            stdscr.addstr(0, 0, f" Settings Saved to {config_file}! ", curses.color_pair(3))
            stdscr.refresh()
            curses.napms(800) 
        elif key == ord('q'):
            break

if __name__ == "__main__":
    curses.wrapper(main)