import enum
import pathlib
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import typing
L = typing.Literal
from xml.etree import ElementTree as ET

PINLENGTH = 15
LINETHICKNESS = 2
CANVASSIZE = 500

IID = str
PinID = int
class Side(enum.Enum):
    Top = 'top'
    Bottom = 'bottom'
    Left = 'left'
    Right = 'right'

class TreeColumns(enum.Enum):
    Side = 'Side'
    PinNumber = 'Pin Number'
    Name = 'Name'

class TreeColumnIndices(enum.Enum):
    Side = 0
    PinNumber = 1
    Name = 2

class PinDef(typing.TypedDict):
    id: PinID
    side: Side
    suppressed: bool

PinLookup = dict[IID, PinDef]
PinCollection = dict[Side, PinLookup]

def getpinsideandid(iid: IID)-> typing.Tuple[Side, PinID]:
    result=iid.split('Pin')
    if len(result) != 2:
        raise ValueError(f"Invalid Pin ID {iid}")
    (side, pinid) = result
    return Side(side), int(result[1])

class ScrolledFrame(ttk.Frame):
    """A pure Tkinter scrollable frame that actually works!

    * Use the 'interior' attribute to place widgets inside the scrollable frame
    * Construct and pack/place/grid normally
    * This frame only allows vertical scrolling
    
    """
    def __init__(self, parent, *args, **kw):
        super().__init__(parent, *args, **kw)

        # create a canvas object and a vertical scrollbar for scrolling it
        self.canvas = canvas = tk.Canvas(self, bd=0, highlightthickness=0)
        canvas.pack(side='left', fill='both', expand=True)
        vscrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        vscrollbar.pack(side='right',fill='y')
        canvas.configure(yscrollcommand=vscrollbar.set)

        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        self.interior = interior = tk.Frame(canvas)
        interior_id = canvas.create_window(0, 0, window=interior,
                                           anchor="nw")

        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(event):
            reqwidth, reqheight = interior.winfo_reqwidth(), interior.winfo_reqheight()
            # update the scrollbars to match the size of the inner frame
            canvas.config(scrollregion=(0, 0, reqwidth, reqheight))
            if reqheight != canvas.winfo_height():
                # update the canvas's width to fit the inner frame
                canvas.config(height=reqheight)
            if reqwidth != canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                canvas.config(width=reqwidth)
        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            width, height = canvas.winfo_width(), canvas.winfo_height()
            if interior.winfo_reqheight() != height:
                # update the inner frame's width to fill the canvas
                canvas.itemconfigure(interior_id, height=height)
            if interior.winfo_reqwidth() != width:
                # update the inner frame's width to fill the canvas
                canvas.itemconfigure(interior_id, width=width)
        canvas.bind('<Configure>', _configure_canvas)

class ICSVGDesigner(tk.Tk):
    def __init__(self):
        super().__init__()

        self.selected: IID = ""

        self.style = ttk.Style()
        self.style.configure("TLabel", font=("Arial", 12, 'bold'))

        self.title("ICSVGDesigner")

        self.pins: PinCollection = {Side.Top: {}, Side.Bottom: {}, Side.Left: {}, Side.Right: {}}

        self.canvas = tk.Canvas(self, bg='white', width=CANVASSIZE, height=CANVASSIZE, scrollregion=(0, 0, CANVASSIZE, CANVASSIZE))
        self.canvas.pack(side='left')

        scrolledframe = ScrolledFrame(self)
        scrolledframe.pack(side='right', fill='y')

        rft = ttk.Frame(scrolledframe.interior)
        rft.pack(side='top')

        ttk.Label(rft, text='IC Width').grid(row=0, column=0, sticky='nsew')
        self.width = tk.IntVar()
        self.width.set(100)
        width = ttk.Spinbox(rft, from_=100, to=1000, increment=1, textvariable=self.width)
        width.grid(row=0, column=1, sticky='nsew')
        ttk.Label(rft, text='IC Height').grid(row=1, column=0, sticky='nsew')
        self.height = tk.IntVar()
        self.height.set(100)
        height = ttk.Spinbox(rft, from_=100, to=1000, increment=1, textvariable=self.height)
        height.grid(row=1, column=1, sticky='nsew')

        ttk.Label(rft, text="Top Pins").grid(row=2, column=0, sticky='nsew')
        self.top_pins = tk.IntVar()
        tp = ttk.Spinbox(rft, from_=0, to=1000, textvariable=self.top_pins)
        tp.grid(row=2, column=1, sticky='nsew')
        ttk.Label(rft, text="Bottom Pins").grid(row=3, column=0, sticky='nsew')
        self.bottom_pins = tk.IntVar()
        bp = ttk.Spinbox(rft, from_=0, to=1000, textvariable=self.bottom_pins)
        bp.grid(row=3, column=1, sticky='nsew')
        ttk.Label(rft, text="Left Pins").grid(row=4, column=0, sticky='nsew')
        self.left_pins = tk.IntVar()
        lp = ttk.Spinbox(rft, from_=0, to=1000, textvariable=self.left_pins)
        lp.grid(row=4, column=1, sticky='nsew')
        ttk.Label(rft, text="Right Pins").grid(row=5, column=0, sticky='nsew')
        self.right_pins = tk.IntVar()
        rp = ttk.Spinbox(rft, from_=0, to=1000, textvariable=self.right_pins)
        rp.grid(row=5, column=1, sticky='nsew')

        rmf = ttk.Frame(scrolledframe.interior)
        rmf.pack(side='top', fill='both', expand=True)

        pf = ttk.Frame(rmf)
        pf.pack(side='top', fill='x', expand=True)

        self.pinnameframe = ttk.Frame(pf)
        ttk.Label(self.pinnameframe, text='Set Pin Name').pack(side='left')
        self.pinname = tk.StringVar()
        self.pinnameentry = ttk.Entry(self.pinnameframe, textvariable=self.pinname)
        self.pinnameentry.pack(side='right', fill='x', expand=True)
        self.pinnameentry.bind('<Return>', self.setpinvalue)
        self.pinnameentry.bind('<KP_Enter>', self.setpinvalue)
        self.pinnameentry.bind('<Escape>', lambda e: self.setpinvalue(None))
        self.pinnameentry.bind('<FocusOut>', self.setpinvalue)

        self.pinnumberframe = ttk.Frame(pf)
        ttk.Label(self.pinnumberframe, text='Set Pin Number').pack(side='left')
        self.pinnumber = tk.IntVar()
        self.pinnumberentry = ttk.Spinbox(self.pinnumberframe, from_=1, to=1000, textvariable=self.pinnumber)
        self.pinnumberentry.pack(side='right', fill='x', expand=True)
        self.pinnumberentry.bind('<Return>', self.setpinvalue)
        self.pinnumberentry.bind('<KP_Enter>', self.setpinvalue)
        self.pinnumberentry.bind('<Escape>', lambda e: self.setpinvalue(None))
        self.pinnumberentry.bind('<FocusOut>', self.setpinvalue)
        
        columns = [column.value for column in TreeColumns.__members__.values()]
        self.tree = ttk.Treeview(rmf, columns=columns, show='headings')
        for label in columns:
            self.tree.heading(label, text=label)

        self.tree.pack(fill='both', expand=True)
        self.tree.bind("<Button-1>", self.selectpin)
        self.tree.bind("<Double-1>", self.showpinedit)
        self.tree.bind("<Escape>", lambda e: self.selectpin(None))
        
        self.exportbutton = ttk.Button(scrolledframe.interior, text='Export', command=self.export)
        self.exportbutton.pack(side='bottom', fill='x')

        self.width.trace_add('write', self.draw)
        self.height.trace_add('write', self.draw)
        self.top_pins.trace_add('write', self.draw)
        self.bottom_pins.trace_add('write', self.draw)
        self.left_pins.trace_add('write', self.draw)
        self.right_pins.trace_add('write', self.draw)

        self.canvas.bind('<Button-1>', self.click)

        self.draw()

    def getpinlocation(self, side: Side, pinnumber: PinID)-> typing.Tuple[float, float]:
        width = self.width.get()
        height = self.height.get()
        xoffset = (CANVASSIZE - width) / 2
        yoffset = (CANVASSIZE - height) / 2
        if side == Side.Top:
            x = xoffset + (width / (self.top_pins.get() + 1)) * (pinnumber + 1)
            y = yoffset
        elif side == Side.Bottom:
            x = xoffset + (width / (self.bottom_pins.get() + 1)) * (pinnumber + 1)
            y = yoffset + height
        elif side == Side.Left:
            x = xoffset
            y = yoffset + (height / (self.left_pins.get() + 1)) * (pinnumber + 1)
        elif side == Side.Right:
            x = xoffset + width
            y = yoffset + (height / (self.right_pins.get() + 1)) * (pinnumber + 1)
        else: raise ValueError(f"Invalid side {side}")
        return x, y

    def draw(self, *args):
        ## The spinboxes may be empty while manually entering the value
        try:
            width = self.width.get()
            height = self.height.get()
            top_pins = self.top_pins.get()
            bottom_pins = self.bottom_pins.get()
            left_pins = self.left_pins.get()
            right_pins = self.right_pins.get()
        except:
            return
            
        self.canvas.delete('all')
        xoffset = (CANVASSIZE - width) / 2
        yoffset = (CANVASSIZE - height) / 2
        self.canvas.create_rectangle(xoffset, yoffset, xoffset + width, yoffset + height, width=LINETHICKNESS)

        for (pins, sides) in [(top_pins, Side.Top), (bottom_pins, Side.Bottom), (left_pins, Side.Left), (right_pins, Side.Right)]:
            for (item, pin) in list(self.pins[sides].items()):
                if pin['id'] >= pins:
                    del self.pins[sides][item]
                    self.tree.delete(item)

        for i in range(top_pins):
            x, y = self.getpinlocation(Side.Top, i)
            pinid = f"{Side.Top.value}Pin{i}"
            if i >= len(self.pins[Side.Top]):
                pin = PinDef(id=i, side=Side.Top, suppressed=False)
                self.tree.insert('', 'end',pinid, values=(Side.Top.value.capitalize(), "", f'Top Pin {i + 1}'))
                self.pins[Side.Top][pinid] = pin
            else:
                pin = self.pins[Side.Top][pinid]
            self.canvas.create_line(x, yoffset, x, yoffset - PINLENGTH, width=LINETHICKNESS, tags=['pin', Side.Top.value, str(i), pinid], fill= "black" if not pin['suppressed'] else "red")
        for i in range(bottom_pins):
            x, y = self.getpinlocation(Side.Bottom, i)
            pinid = f"{Side.Bottom.value}Pin{i}"
            if i >= len(self.pins[Side.Bottom]):
                pin = PinDef(id=i, side=Side.Bottom, suppressed=False)
                self.tree.insert('', 'end', pinid, values=(Side.Bottom.value.capitalize(), "", f'Bottom Pin {i + 1}'))
                self.pins[Side.Bottom][pinid] = pin
            else:
                pin = self.pins[Side.Bottom][pinid]
            self.canvas.create_line(x, yoffset + height, x, yoffset + height + PINLENGTH, width=LINETHICKNESS, tags=['pin', Side.Bottom.value, str(i), pinid], fill= "black" if not pin['suppressed'] else "red")
        for i in range(left_pins):
            x, y = self.getpinlocation(Side.Left, i)
            pinid = f"{Side.Left.value}Pin{i}"
            if i >= len(self.pins[Side.Left]):
                pin = PinDef(id=i, side=Side.Left, suppressed=False)
                self.tree.insert('', 'end', pinid, values=(Side.Left.value.capitalize(), "", f'Left Pin {i + 1}'))
                self.pins[Side.Left][pinid] = pin
            else:
                pin = self.pins[Side.Left][pinid]
            self.canvas.create_line(xoffset, y, xoffset - PINLENGTH, y, width=LINETHICKNESS, tags=['pin', Side.Left.value, str(i), pinid], fill= "black" if not pin['suppressed'] else "red")
        for i in range(right_pins):
            x, y = self.getpinlocation(Side.Right, i)
            pinid = f"{Side.Right.value}Pin{i}"
            if i >= len(self.pins[Side.Right]):
                pin = PinDef(id=i, side=Side.Right, suppressed=False)
                self.tree.insert('', 'end', pinid, values=(Side.Right.value.capitalize(), "", f'Right Pin {i + 1}'))
                self.pins[Side.Right][pinid] = pin
            else:
                pin = self.pins[Side.Right][pinid]
            self.canvas.create_line(xoffset + width, y, xoffset + width + PINLENGTH, y, width=LINETHICKNESS, tags=['pin', Side.Right.value, str(i), pinid], fill= "black" if not pin['suppressed'] else "red")

        overallx = width + 4 * PINLENGTH
        xscale = CANVASSIZE / overallx
        overally = height + 4 * PINLENGTH
        yscale = CANVASSIZE / overally

        self.canvas.scale('all', CANVASSIZE/2, CANVASSIZE/2, min(xscale, yscale), min(xscale, yscale))
        self.sortTree()

    def sortTree(self):
        if not self.tree.get_children(''): return
        sortorder = list(Side.__members__.keys())
        data = [(item,self.tree.item(item, "values")) for item in self.tree.get_children('')]
        data.sort(key = lambda item: item[0] )
        data.sort(key = lambda item: sortorder.index(item[1][TreeColumnIndices.Side.value]))
        for i, item in enumerate(data):
            self.tree.move(item[0], '', i)

    def click(self, event):
        x, y = event.x, event.y
        items = self.canvas.find_closest(x, y)
        if not items: return
        item = items[0]
        tags = self.canvas.gettags(item)
        if 'pin' in tags:
            side, pinid = tags[1], tags[3]
            side = Side(side)
            pin = self.pins[side][pinid]
            pin['suppressed'] = not pin['suppressed']
            if not pin['suppressed']:
                self.canvas.itemconfig(item, fill='black')
            else:
                self.canvas.itemconfig(item, fill='red')

        self.canvas.update()

    def gettreepin(self, event)-> tuple[IID, list[str]]:
        item = self.tree.identify('item', event.x, event.y)
        if not item: return  ## type: ignore tree.identify is not typed

        return (item, self.tree.item(item)['values'])  ## type: ignore tree.item doesn't have overloads defined afaict
    
    def selectpin(self, event):
        for item in self.canvas.find_withtag('selected'):
            tags = self.canvas.gettags(item)
            side = tags[1]
            side = Side(side)
            pinid = tags[3]
            self.canvas.itemconfig(item, fill = 'black' if not self.pins[side][pinid]['suppressed'] else 'red')
            self.canvas.dtag(item, 'selected')
        if not event: return self.canvas.update()
        self.tree.selection_remove(self.tree.selection())
        result = self.gettreepin(event)
        if not result: return self.canvas.update()
        (piniid, pin) = result
        self.tree.selection_set(self.tree.identify_row(y=event.y))
        self.canvas.addtag_withtag('selected', piniid)
        self.canvas.itemconfig("selected", fill='blue')
        self.canvas.update()

    def showpinedit(self, event):
        result = self.gettreepin(event)
        if not result: return
        (pinid, (side, pinnumber, name)) = result
        self.pinname.set(name)
        self.pinnumber.set(int(pinnumber) if pinnumber else 0)
        columnid = self.tree.identify_column(event.x)
        if columnid == '#2':
            try:
                pinnumber = int(pinnumber)
            except:
                pinnumber = 1            
            self.pinnumberframe.pack(side='top', fill='x')
            self.pinnumberentry.focus()
            self.pinnumberentry.selection_range(0, 'end')
            self.selected = pinid
            self.pinnumber.set(pinnumber)
        elif columnid == '#3':
            self.pinnameframe.pack(side='top', fill='x')
            self.pinnameentry.focus()
            self.pinnameentry.selection_range(0, 'end')
            self.selected = pinid
            self.pinname.set(name)

    def setpinvalue(self, event):
        if not event:
            self.selected = ""
            self.pinnumberframe.pack_forget()
            return self.pinnameframe.pack_forget()
        ## If the pinnameentry is managed, then we're setting the name
        isname = bool(self.pinnameframe.winfo_manager())
        pinid = self.selected
        if not pinid:
            self.pinnumberframe.pack_forget()
            return self.pinnameframe.pack_forget()
        if isname:
            newname = self.pinname.get()
            if not newname:
                side, number = getpinsideandid(pinid)
                newname = f"{side.name} Pin {number}"
            self.tree.set(pinid, TreeColumns.Name.value, newname)
            self.selected = ""
            self.pinnameframe.pack_forget()
        else:
            try:
                newnumber = self.pinnumber.get()
            except:
                newnumber = ""
            self.tree.set(pinid, TreeColumns.PinNumber.value, newnumber) ## type:ignore
            self.selected = ""
            self.pinnumberframe.pack_forget()

    def export(self):
        ## Need to check pinnumbers before asking for file name
        items = self.tree.get_children('')
        pinnumbers = dict()
        for item in items:
            treevals = self.tree.item(item)['values']
            pinnumber = treevals[TreeColumnIndices.PinNumber.value]
            if not pinnumber: continue
            if pinnumber in pinnumbers:
                pinnumbers[pinnumber].append(treevals[TreeColumnIndices.Name.value])
            else:
                pinnumbers[pinnumber] = [treevals[TreeColumnIndices.Name.value]]

        output = []
        for (pinnumber, pins) in pinnumbers.items():
            if len(pins) > 1:
                output.append(f"Pin Number {pinnumber} is used by {', '.join(pins)}")

        if output:
            messagebox.showerror("Duplicate Pin Numbers", "\n".join(output))
            return

        filename = filedialog.asksaveasfilename(defaultextension='.svg', filetypes=[('SVG Files', '*.svg')])
        if not filename: return
        txtpath = pathlib.Path(filename)
        txtpath = txtpath.with_suffix('.txt')
        if(txtpath.exists() and not messagebox.askyesno("Overwrite?", f"{txtpath} already exists. Overwrite?")):
            return

        width = self.width.get()
        height = self.height.get()
        overallwidth = width + 2 * PINLENGTH
        overallheight = height + 2 * PINLENGTH

        root = ET.Element('svg', xmlns='http://www.w3.org/2000/svg', version='1.1', width=str(overallwidth), height=str(overallheight), viewBox=f"0 0 {overallwidth} {overallheight}")

        ## NOTE- because stroke-width is hyphenated it must be passed as part of a destructured dictionary
        ET.SubElement(root, 'rect', x=str(PINLENGTH), y=str(PINLENGTH), width=str(width), height=str(height), stroke="black", fill="none", **{"stroke-width":"1"}) ## type:ignore ## Not sure about why this is an error because it works

        pinlocations0 = ["Pin Locations from Top-Left:"]
        pinlocationscenter = ["Pin Locations from Center:"]
        
        for side in Side.__members__.values():
            pinlocations0.append(f"\t{side.name} Pins:")
            pinlocationscenter.append(f"\t{side.name} Pins:")
            pins = getattr(self, side.value + '_pins').get()
            spacing = 0
            if side in [Side.Top, Side.Bottom]:
                spacing = width / (pins + 1)
            else:
                spacing = height / (pins + 1)
            for (pinid, pin) in self.pins[side].items():
                if pin['suppressed']: continue
                ## X and Y should be the end of the pin
                x = y = deltax = deltay = 0
                if side == Side.Top:
                    x = PINLENGTH+spacing * (pin['id'] + 1)
                    y = 0
                    deltax = 0
                    deltay = PINLENGTH
                elif side == Side.Bottom:
                    x = PINLENGTH+spacing * (pin['id'] + 1)
                    y = overallheight-PINLENGTH
                    deltax = 0
                    deltay = PINLENGTH
                elif side == Side.Left:
                    x = 0
                    y = PINLENGTH+spacing * (pin['id'] + 1)
                    deltax = PINLENGTH
                    deltay = 0
                elif side == Side.Right:
                    x = overallwidth
                    y = PINLENGTH+spacing * (pin['id'] + 1)
                    deltax = -PINLENGTH
                    deltay = 0

                treeviewvals = self.tree.item(pinid)['values']
                name = treeviewvals[TreeColumnIndices.Name.value]
                namestring = ""
                if name: namestring= f" ({name})"
                else: name = f"{side.name} Pin {pin['id'] + 1}"
                pinnumber = treeviewvals[TreeColumnIndices.PinNumber.value]
                if not pinnumber:
                    pinnumber = pin['id'] + 1
                    pinnumberstring = f"{side.name} Pin {pinnumber}"
                else:
                    pinnumberstring = f"Pin {pinnumber}"
                pinlocations0.append(f"\t\t{pinnumberstring}{namestring}: ({x}, {y})")
                xfromcenter = x - overallwidth / 2
                yfromcenter = y - overallheight / 2
                pinlocationscenter.append(f"\t\t{pinnumberstring}{namestring}: ({xfromcenter}, {yfromcenter})")

                ET.SubElement(root, 'line', id=f"{name}", x1=str(x), y1=str(y), x2=str(x + deltax), y2=str(y + deltay), stroke="black", **{"stroke-width":"1"}) ## type:ignore ## Not sure about why this is an error because it works

        tree = ET.ElementTree(root)
        with open(filename, 'wb') as f:
            f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
            tree.write(f)

        with open(txtpath, 'w') as f:
            f.write("\n".join(pinlocations0))
            f.write("\n\n")
            f.write("\n".join(pinlocationscenter))

        messagebox.showinfo("Exported", f"Exported to {filename}")

if __name__ == "__main__":
    app = ICSVGDesigner()
    iconpath = pathlib.Path(__file__).parent / 'icon.ico'
    if iconpath.exists():
        app.iconbitmap(iconpath)
    app.mainloop()