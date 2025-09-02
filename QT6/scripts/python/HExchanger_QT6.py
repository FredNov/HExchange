from PySide6 import QtWidgets
import hou, re,os, glob, shutil

class UIExchange (QtWidgets.QWidget):

    def __init__(self):

        QtWidgets.QWidget.__init__(self)

        self.resize(295, 193)
        main = QtWidgets.QVBoxLayout()
        pathLayout = QtWidgets.QHBoxLayout()
        saveLayout = QtWidgets.QHBoxLayout()
        saveLayout.setSpacing(10)
        btnLayout = QtWidgets.QHBoxLayout()
        self.ln_path = QtWidgets.QLineEdit()
        self.ln_name = QtWidgets.QLineEdit()
        self.coll = QtWidgets.QCheckBox('Collect with source files:')
        self.coll.setChecked(True)
        self.btn_B_file = QtWidgets.QToolButton()
        self.btn_B_file.setText('...')
        self.btn_db = QtWidgets.QToolButton()
        self.btn_db.setText('Dropbox')
        self.nd_view = QtWidgets.QTreeWidget()
        self.nd_view.setColumnCount(1)
        self.nd_view.setHeaderLabels(['Nodes'])
        self.nd_view.setIndentation(0)
        self.nd_view.setItemsExpandable(0)
        self.btn_del = QtWidgets.QPushButton()
        self.btn_set = QtWidgets.QPushButton()
        self.btn_get = QtWidgets.QPushButton()
        self.btn_upd = QtWidgets.QPushButton()
        ptsrv=hou.getenv('HIP')+'/exchange_Nodes'
        self.ln_path.setText(ptsrv)
        self.ln_path.setDisabled(1)
        pathLayout.addWidget(self.coll)
        pathLayout.addWidget(self.ln_path)
        pathLayout.addWidget(self.btn_B_file)
        pathLayout.addWidget(self.btn_db)
        saveLayout.addWidget(self.btn_get)
        saveLayout.addWidget(self.btn_set)
        saveLayout.addWidget(self.btn_upd)
        saveLayout.addWidget(self.btn_del)
        main.addLayout(pathLayout)
        main.addWidget(self.ln_name)
        main.addWidget(self.nd_view)
        main.addLayout(saveLayout)

        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        main.addItem(spacerItem)
        self.setWindowTitle("Form")
        self.ln_name.setText(hou.hipFile.basename()[:-4])
        self.btn_del.setText("Delete")
        self.btn_set.setText("Save")
        self.btn_get.setText("Load")
        self.btn_upd.setText("Update")
        self.btn_B_file.clicked.connect(self.setFilePath)
        self.btn_db.clicked.connect(self.set_dropbox_path)
        self.btn_set.clicked.connect(self.exchangeSet)
        self.btn_get.clicked.connect(self.exchangeGet)
        self.btn_upd.clicked.connect(self.updateList)
        self.btn_del.clicked.connect(self.deleteItem)
        self.setLayout(main)
        self.setProperty("houdiniStyle", True)
        self.updateList()

    def setFilePath(self):
        ospath = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Path to Save", self.ln_path.text())
        if ospath:
        	self.ln_path.setText(ospath) 
        self.updateList()
    
    def checkExceptions(self,param):
        pth=param.eval()
        add=0
        exceptNames= ['default.bgeo','defcam.bgeo','pointlight.bgeo','defgeo.bgeo','`opinputpath','op:','./sdf0000.simdata']
        if pth!='' and len(param.keyframes())==0 and (not param.isAtDefault()) and (not param.isLocked()) and (not param.isDisabled()) and (not param.isHidden()):
            pth=param.unexpandedString()
            ptheval=param.eval()
            add=1
            for ex in exceptNames:
                if pth.find(ex)==0:
                    add=0
                k=pth.split('/')
                if k[len(k)-1].find(ex)==0 :
                    add=0
        return add

    def convToHip(self, pth):
        pth=pth.replace('\\','/')
        pth=pth.replace(hou.getenv('HIP'),'$HIP')
        if hou.getenv('JOB'):
            if os.path.exists(hou.getenv('JOB')):
                pth=pth.replace(hou.getenv('JOB'),'$JOB')
        return pth  

    def correctWrongExpr(self,parm):
        path=parm.eval()
        if path.find(r'<UDIM>')!=-1 or path.find(r'<udim>')!=-1:
            path=re.sub(r'<UDIM>','????',path)
            path=re.sub(r'<udim>','????',path)
        if path.find(r'#')!=-1:    
            path=re.sub(r'#.+','',path)
        detect=re.findall(r'[\^\*\+\{\}\[\]\|"\'~%&<>`]',path)
        if len(detect)>0:
            print('Special symbols detected (maybe unsupported expression) in file path \"'+ parm.path() +'\" suspicious symbol \"'+''.join(detect)+'\" .IF THE FILE IS NOT PROCESSED you can debug from here. You can e-mail to gammany@gmail.com to support more expressions.\n')
        return path 

    def findFiles(self,parm,path):
        files=[]
        path=os.path.normcase(path)
        pth=self.correctWrongExpr(parm)
        fil = os.path.basename(pth)
        if parm.isTimeDependent():
            filePattern=re.sub(r'\d','?',fil)
        else:
            filePattern=fil
        ch_search='\\'.join([path, filePattern])
        files=glob.glob(ch_search)
        return files 
    
    def copyFiles(self,params,arg_path):
        if len(params)>0:
            for p in params:
                try:
                    oldpath=p.unexpandedString()
                    files=self.findFiles(p, os.path.dirname(p.eval()))
                    if len(files)>0: 
                        for file in files:
                            newPath = '\\'.join([arg_path,os.path.basename(file)])
                            if not os.path.exists(newPath):
                                shutil.copy2(file, newPath)
                            print(newPath+' collected')
                        oldExpr=re.split(r'[/\\]',p.unexpandedString())
                        oldExpr.reverse()
                        newParam='/'.join([arg_path , oldExpr[0]])
                        p.set(newParam)
                    else:
                        erstr='File '+p.unexpandedString()+' on node '+p.node().name()+' in parameter '+p.path()+' NOT FOUND \n'
                        print(erstr)
                except BaseException as e:
                    erstr='ERROR on node '+p.node().name()+'\n'
                    erstr+=str(e)
                    print(erstr)

    def exchangeSet(self):
        if hou.hipFile.hasUnsavedChanges():
            if hou.ui.displayConfirmation('The file has unsaved changes. SAVE?'):
                hou.hipFile.save()
            else:
                pass
        ppp=hou.hipFile.path()
        selNodes=hou.selectedNodes()

        if len(selNodes)==0:
            hou.ui.displayMessage('No selection') 
            return -1

        parent=selNodes[0].parent() 
        if parent.type().name()!='obj':
            hou.ui.displayMessage('This must be an object on top level') 
            return -1

        arg_path=os.path.normcase(self.ln_path.text()+'/'+self.ln_name.text())
        if not os.path.exists(arg_path):
            os.makedirs(arg_path)

        if arg_path:
            nodes=[]
            for n in selNodes:
                nodes.extend(n.allSubChildren(True))
            params=[] 
            for n in nodes:
                nodepar=n.globParms('*file* *out*')
                for arg_parm in nodepar:
                    if arg_parm.parmTemplate().dataType()==hou.parmData.String:
                        if self.checkExceptions(arg_parm)!=0:
                            params.append(arg_parm)

            if self.coll.isChecked():
                self.copyFiles(params,arg_path)   

            parent.saveItemsToFile(selNodes, arg_path+'/nodes.hip')
            self.updateList()
            hou.hipFile.load(ppp, True, True)

    def exchangeGet(self):
        item=self.nd_view.selectedItems()[0]
        if item.childCount()==0:
            item=item.parent()
        path=os.path.normcase(self.ln_path.text())+'\\'+item.text(0)+'\\'+'nodes.hip'
        hou.node('/obj').loadItemsFromFile(path, ignore_load_warnings=False)
        self.updateList()

    def updateList(self):      
        path=os.path.normcase(self.ln_path.text())
        dirs=glob.glob(path+'\\*/')
        self.nd_view.clear()
        for d in dirs:
            item=QtWidgets.QTreeWidgetItem(self.nd_view,[os.path.basename(os.path.dirname(d))])
            files=os.listdir(d)
            for f in files:
                QtWidgets.QTreeWidgetItem(item,[f])

    def deleteItem(self):
        selected_items = self.nd_view.selectedItems()
        if not selected_items:
            hou.ui.displayMessage('No item selected')
            return -1
        item = selected_items[0]
        if item.childCount()==0:
            item=item.parent()
        path=os.path.normcase(self.ln_path.text())+'\\'+item.text(0)
        if hou.ui.displayConfirmation('The Item '+item.text(0)+' will be deleted!'):
            pass
        else:
            return -1
        print(path+' DELETED')
        root = self.nd_view.invisibleRootItem()
        root.removeChild(item)
        shutil.rmtree(path)
        self.updateList()

# ------------------------------------------------------------------------------------------

    def _get_appdata_path(self):
        import ctypes
        from ctypes import wintypes, windll
        CSIDL_LOCAL_APPDATA = 28
        _SHGetFolderPath = windll.shell32.SHGetFolderPathW
        _SHGetFolderPath.argtypes = [wintypes.HWND,
                                     ctypes.c_int,
                                     wintypes.HANDLE,
                                     wintypes.DWORD,
                                     wintypes.LPCWSTR]
        path_buf = wintypes.create_unicode_buffer(wintypes.MAX_PATH)
        result = _SHGetFolderPath(0, CSIDL_LOCAL_APPDATA, 0, 0, path_buf)
        return path_buf.value

    def dropbox_home(self):
        from platform import system
        import base64
        import os.path
        _system = system()
        if _system in ('Windows', 'cli'):
            host_db_path = os.path.join(self._get_appdata_path(),
                                        'Dropbox',
                                        'host.db')
        elif _system in ('Linux', 'Darwin'):
            host_db_path = os.path.expanduser('~'
                                              '/.dropbox'
                                              '/host.db')
        else:
            raise RuntimeError('Unknown system={}'
                               .format(_system))
        if not os.path.exists(host_db_path):
            raise RuntimeError("Config path={} doesn't exists"
                               .format(host_db_path))
        with open(host_db_path, 'r') as f:
            data = f.read().split()
        
        return base64.b64decode(data[1]).decode('utf-8')

    def set_dropbox_path(self):
        if self.btn_db.text()=='Dropbox':
            ln=self.convToHip(self.dropbox_home()+'\\exchange_Nodes')
            self.ln_path.setText(ln)
            self.btn_db.setText('Local')
        else:
            ptsrv=hou.getenv('HIP')+'/exchange_Nodes'
            self.ln_path.setText(ptsrv)
            self.btn_db.setText('Dropbox')
        self.updateList()
