#@+leo-ver=5-thin
#@+node:ekr.20110605121601.17996: * @file ../plugins/qt_commands.py
'''Leo's Qt-related commands defined by @g.command.'''
import leo.core.leoGlobals as g
import leo.core.leoColor as leoColor
import leo.core.leoConfig as leoConfig
from leo.core.leoQt import QtGui, QtWidgets
#@+others
#@+node:ekr.20110605121601.18000: ** init
def init():
    '''Top-level init function for qt_commands.py.'''
    ok = True
    g.plugin_signon(__name__)
    g.registerHandler("select2", onSelect)
    return ok

def onSelect(tag, keywords):
    c = keywords.get('c') or keywords.get('new_c')
    wdg = c.frame.top.leo_body_frame
    wdg.setWindowTitle(c.p.h)
#@+node:ekr.20110605121601.18001: ** qt: detach-editor-toggle & helpers
@g.command('detach-editor-toggle')
def detach_editor_toggle(event):
    """ Detach or undetach body editor """
    c = event['c']
    detach = True
    try:
        if c.frame.detached_body_info is not None:
            detach = False
    except AttributeError:
        pass
    if detach:
        detach_editor(c)
    else:
        undetach_editor(c)

@g.command('detach-editor-toggle-max')
def detach_editor_toggle_max(event):
    """ Detach editor, maximize """
    c = event['c']
    detach_editor_toggle(event)
    if c.frame.detached_body_info is not None:
        wdg = c.frame.top.leo_body_frame
        wdg.showMaximized()
#@+node:ekr.20170324145714.1: *3* qt: detach_editor
def detach_editor(c):
    wdg = c.frame.top.leo_body_frame
    parent = wdg.parent()
    if parent is None:
        # just show if already detached
        wdg.show()
    else:
        c.frame.detached_body_info = parent, parent.sizes()
        wdg.setParent(None)
        sheet = c.config.getData('qt-gui-plugin-style-sheet')
        if sheet:
            sheet = '\n'.join(sheet)
            wdg.setStyleSheet(sheet)
        wdg.show()
#@+node:ekr.20170324145716.1: *3* qt: undetach_editor
def undetach_editor(c):
    wdg = c.frame.top.leo_body_frame
    parent, sizes = c.frame.detached_body_info
    parent.insertWidget(0, wdg)
    wdg.show()
    parent.setSizes(sizes)
    c.frame.detached_body_info = None
#@+node:tbrown.20140620095406.40066: ** qt: gui-show/hide/toggle
# create the commands gui-<menu|iconbar|statusbar|minibuffer>-<hide|show>
widgets = [
    ('menu', lambda c: c.frame.top.menuBar()),
    ('iconbar', lambda c: c.frame.top.iconBar),
    ('statusbar', lambda c: c.frame.top.statusBar),
    ('minibuffer', lambda c: c.frame.miniBufferWidget.widget.parent()),
    ('tabbar', lambda c: g.app.gui.frameFactory.masterFrame.tabBar()),
]
for vis in 'hide', 'show', 'toggle':
    for name, widget in widgets:

        def dovis(event, widget=widget, vis=vis):
            c = event['c']
            w = widget(c)
            if vis == 'toggle':
                vis = 'hide' if w.isVisible() else 'show'
            # Executes either w.hide() or w.show()
            getattr(w, vis)()

        g.command("gui-%s-%s" % (name, vis))(dovis)

    def doall(event, vis=vis):
        c = event['c']
        for name, widget in widgets:
            w = widget(c)
            if vis == 'toggle':
                # note, this *intentionally* toggles all to on/off
                # based on the state of the first
                vis = 'hide' if w.isVisible() else 'show'
            getattr(w, vis)()

    g.command("gui-all-%s" % vis)(doall)
#@+node:ekr.20140918124632.17893: ** qt: show-style-sheet
@g.command('show-style-sheet')
def print_style_sheet(event):
    '''show-style-sheet command.'''
    c = event.get('c')
    if c:
        c.styleSheetManager.print_style_sheet()
#@+node:ekr.20170324143944.2: ** qt: show-color-names
@g.command('show-color-names')
def showColorNames(event=None):
    '''Put up a dialog showing color names.'''
    c = event.get('c')
    template = '''
        QComboBox {
            background-color: %s;
            selection-background-color: %s;
            selection-color: black;
        }'''
    ivar = 'leo_settings_color_picker'
    if getattr(c, ivar, None):
        g.es('The color picker already exists in the icon bar.')
    else:
        color_list = []
        box = QtWidgets.QComboBox()

        def onActivated(n,*args,**keys):
            color = color_list[n]
            sheet = template % (color,color)
            box.setStyleSheet(sheet)
            g.es("copied to clipboard:", color)
            QtWidgets.QApplication.clipboard().setText(color)

        box.activated.connect(onActivated)
        color_db = leoColor.leo_color_database
        for key in sorted(color_db):
            if not key.startswith('grey'): # Use gray, not grey.
                val = color_db.get(key)
                color = QtGui.QColor(val)
                color_list.append(val)
                pixmap = QtGui.QPixmap(40,40)
                pixmap.fill(color)
                icon = QtGui.QIcon(pixmap)
                box.addItem(icon,key)

        c.frame.iconBar.addWidget(box)
        setattr(c,ivar,True)
        g.es('created color picker in icon area')
            # Do this last, so errors don't prevent re-execution.
#@+node:ekr.20170324142416.1: ** qt: show-color-wheel
@g.command('show-color-wheel')
def showColorWheel(self, event=None):
    '''Show a Qt color dialog.'''
    c = self.c; p = c.p
    picker = QtWidgets.QColorDialog()
    in_color_setting = p.h.startswith('@color ')
    try:
        text = QtWidgets.QApplication.clipboard().text()
        if in_color_setting:
            text = p.h.split('=', 1)[1].strip()
        color = QtGui.QColor(text)
        picker.setCurrentColor(color)
    except (ValueError, IndexError) as e:
        g.trace('error caught', e)
    if not picker.exec_():
        g.es("No color selected")
    elif in_color_setting:
        udata = c.undoer.beforeChangeNodeContents(p)
        p.h = '%s = %s'%(p.h.split('=', 1)[0].strip(),
                         g.u(picker.selectedColor().name()))
        c.undoer.afterChangeNodeContents(p, 'change-color', udata)
    else:
        text = picker.selectedColor().name()
        g.es("copied to clipboard:", text)
        QtWidgets.QApplication.clipboard().setText(text)
#@+node:ekr.20170324143944.3: ** qt: show-fonts
@g.command('show-fonts')
def showFonts(self, event=None):
    '''Open a tab in the log pane showing a font picker.'''
    c = self.c; p = c.p

    picker = QtWidgets.QFontDialog()
    if p.h.startswith('@font'):
        (name, family, weight, slant, size) = leoConfig.parseFont(p.b)
    else:
        name, family, weight, slant, size = None, None, False, False, 12
    try:
        font = QtGui.QFont()
        if family: font.setFamily(family)
        font.setBold(weight)
        font.setItalic(slant)
        font.setPointSize(size)
        picker.setCurrentFont(font)
    except ValueError:
        pass
    if not picker.exec_():
        g.es("No font selected")
    else:
        font = picker.selectedFont()
        udata = c.undoer.beforeChangeNodeContents(p)
        comments = [x for x in g.splitLines(p.b) if x.strip().startswith('#')]

        defs = [
            '\n' if comments else '',
            '%s_family = %s\n'%(name, font.family()),
            '%s_weight = %s\n'%(name, 'bold' if font.bold() else 'normal'),
            '%s_slant = %s\n'%(name, 'italic' if font.italic() else 'roman'),
            '%s_size = %s\n'%(name, font.pointSizeF())
        ]

        p.b = g.u('').join(comments + defs)
        c.undoer.afterChangeNodeContents(p, 'change-font', udata)
#@+node:ekr.20140918124632.17891: ** qt: style-reload
@g.command('style-reload')
@g.command('reload-style-sheets')
def style_reload(event):
    """reload-styles command.

    Find the appropriate style sheet and re-apply it.

    This replaces execution of the `stylesheet & source` node in settings files.
    """
    c = event.get('c')
    if c and c.styleSheetManager:
        c.reloadSettings()
            # Call ssm.reload_settings after reloading all settings.
#@+node:ekr.20140918124632.17892: ** qt: style-set-selected
@g.command('style-set-selected')
def style_set_selected(event):
    '''style-set-selected command. Set the global stylesheet to c.p.b. (For testing)'''
    c = event.get('c')
    if c:
        c.styleSheetManager.set_selected_style_sheet()
#@+node:ekr.20181009123539.1: ** qt: toggle-gutter
@g.command('add-gutter')
def add_gutter(event):
    '''Add the gutter area showing line numbers.'''
    c = event.get('c')
    if not c:
        return
    dw = c.frame.top
    gutter = dw.gutter
    glayout = dw.gutter_layout
    if gutter.using_gutter:
        # NumberBar has a reference to gutter.edit.
        # Apparently, this causes problems.
        pass
        # glayout.removeWidget(gutter.edit)
        # glayout.removeWidget(gutter.number_bar)
        # glayout.invalidate()
        # glayout.parent().layout().invalidate()
        # glayout.addWidget(dw.gutter.edit)
        # gutter.using_gutter = False
    else:
        glayout.removeWidget(gutter.edit)
        glayout.addWidget(gutter.number_bar)
        glayout.addWidget(gutter.edit)
        gutter.using_gutter = True
#@-others
#@@language python
#@@tabwidth -4
#@@pagewidth 70
#@-leo
