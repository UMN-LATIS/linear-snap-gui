# stdlib
import configparser
import sys
import pathlib
import os
# 3rd party
import appdirs

homedir = pathlib.Path.home()
class LSConfig:
    
    configValues = {}

    def __init__(self):
        self.configfile = pathlib.Path(appdirs.user_config_dir("LinearSnap")) / "config.ini"
        self.Config = configparser.ConfigParser()
        
        if not self.configfile.is_file():
            print("Creating Configuration file")
            self.__load_defaults()
        else:
            print("Loading Internal Configuration")
            self._load_from_file()
            
    def __load_defaults(self):
        # Touch file
        isExist = os.path.exists(self.configfile.parent)
        if not isExist:
            os.makedirs(self.configfile.parent)

        self.configfile.write_text("""
[General]
[Processing]
[FocusStack]
        """)
        
        self._load_from_file()
        return
    
    def _load_from_file(self):
        self.Config.read(self.configfile)
        
        if "General" not in self.Config:
            self.Config["General"] = {}
        if "Processing" not in self.Config:
            self.Config["Processing"] = {}
        if "FocusStack" not in self.Config:
            self.Config["FocusStack"] = {}
        if "Camera" not in self.Config:
            self.Config["Camera"] = {}
            
        self.configValues["BasePath"] = self.Config.get("General", "BasePath", fallback=str(homedir.absolute()))
        self.configValues["ArchivePath"] = self.Config.get("General", "ArchivePath", fallback=str(homedir.absolute()))
        self.configValues["CoreOutputPath"] = self.Config.get("General", "CoreOutputPath", fallback=str(homedir.absolute()))
        # self.configValues["VignetteMagic"] = self.Config.get("Processing", "VignetteMagic", fallback="1.1")
        # self.configValues["FocusStackInstall"] = self.Config.get("FocusStack", "Install", fallback=str(homedir.absolute()))
        # self.configValues["FocusStackLaunchPath"] = self.Config.get("FocusStack", "LaunchPath", fallback='"{{Install}}" --consistency=0 --align-keep-size --no-whitebalance --no-contrast --jpgquality=100 --output="{{outputPath}}" "{{folderPath}}/"*jpg')
        self.configValues["StartPositionBig"] = self.Config.get("Processing", "StartPositionBig", fallback="220")
        self.configValues["StartPositionSmall"] = self.Config.get("Processing", "StartPositionSmall", fallback="470")
        self.configValues["StackDepth"] = self.Config.get("Processing", "StackDepth", fallback="20")
        self.configValues["Overlap"] = self.Config.get("Processing", "Overlap", fallback="150")
        self.configValues["Refocus"] = self.Config.get("Processing", "Refocus", fallback="15")
        self.configValues["captureISO"] = self.Config.get("Camera", "captureISO", fallback="100")
        self.configValues["captureShutter"] = self.Config.get("Camera", "captureShutter", fallback="1/500")
        self.configValues["previewISO"] = self.Config.get("Camera", "previewISO", fallback="100")
        self.configValues["previewShutter"] = self.Config.get("Camera", "previewShutter", fallback="1/15")
        self.configValues["CoreType"] = self.Config.get("General", "CoreType", fallback="0")
        self.configValues["SerialPort"] = self.Config.get("General", "SerialPort", fallback="")
            
    def save_config(self):

        # Configuration
        self.Config.set("General", "BasePath", self.configValues["BasePath"])
        self.Config.set("General", "ArchivePath", self.configValues["ArchivePath"])
        self.Config.set("General", "CoreOutputPath",self.configValues["CoreOutputPath"])
        self.Config.set("General", "CoreType",self.configValues["CoreType"])
        self.Config.set("General", "SerialPort",self.configValues["SerialPort"])

        # self.Config.set("Processing", "VignetteMagic",self.configValues["VignetteMagic"])
        self.Config.set("Processing", "StartPositionBig",self.configValues["StartPositionBig"])
        self.Config.set("Processing", "StartPositionSmall",self.configValues["StartPositionSmall"])
        self.Config.set("Processing", "StackDepth",self.configValues["StackDepth"])
        self.Config.set("Processing", "Overlap",self.configValues["Overlap"])
        self.Config.set("Processing", "Refocus",self.configValues["Refocus"])
        
        # self.Config.set("FocusStack", "Install",self.configValues["FocusStackInstall"])
        # self.Config.set("FocusStack", "LaunchPath",self.configValues["FocusStackLaunchPath"])
        
        self.Config.set("Camera", "captureISO",self.configValues["captureISO"])
        self.Config.set("Camera", "captureShutter",self.configValues["captureShutter"])
        self.Config.set("Camera", "previewISO",self.configValues["previewISO"])
        self.Config.set("Camera", "previewShutter",self.configValues["previewShutter"])
        
        with open(self.configfile, "w") as f:
            self.Config.write(f)


if __name__ == "__main__":
    sys.exit(1)