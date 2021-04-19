import ftplib
from ftplib import FTP
from contextlib import closing
import sys, os


__PATH__ = os.path.realpath("")

class FileStorage:
    def __init__(self, server = "ftp.drivehq.com", usr = "tecnosam", pwd = "I$AAc1023", persist = False):
        # self.ftp = FTP( server )
        # self.ftp.login( usr, pwd )
        self.ftp = FTP( "localhost" )
        self.ftp.login( "nb", "isaac1023" )
        self.persist = persist
    def backup( self, d = "/pp" ):
        for i in os.listdir( "pp" ):
            with open( f"pp/{i}", "rb" ) as f:
                self.save_file( f, d = d )
        return True
    def restore(self, d = '/pp'):
        os.chdir("pp")
        for i in self.listfiles( d ):
            self.download( i, d )
        os.chdir( ".." )
        return True
    def listdir(self, d = '/pp'):
        try:
            self.ftp.cwd( d )
            files = []
            self.ftp.dir(files.append)
            return files
        except ftplib.all_errors as e:
            raise e
        if not self.persist:
            self.ftp.close()
    def listfiles(self, d = '/pp'):
        try:
            self.ftp.cwd( d )
            files = list ( self.ftp.nlst ( d ) )
            return files
        except ftplib.all_errors as e:
            raise e
        if not self.persist:
            self.ftp.close()
    def mkdir(self, dn):
        try:
            self.ftp.mkd(dn)
        except ftplib.all_errors as e:
            raise e
        if not self.persist:
            self.ftp.close()

    def save_file(self, f, d = '/pp'):
        filename = f.name.split("/")[-1]
        try:
            with f as fp:
                try:
                    self.mkdir( d )
                except ftplib.error_perm:
                    pass
                self.ftp.cwd( d )
                res = self.ftp.storbinary("STOR " + f"{filename}" , fp)
                if not res.startswith('226 Transfer complete'):
                    return False
            fp.close()
        except ftplib.all_errors as e:
            raise e
        if not self.persist:
            self.ftp.close()
        return True

    def download(self, f, d = '/pp'):
        jj = os.listdir(os.path.realpath(""))
        if (f in jj):
            return True
        filename = f.split("/")[-1]
        try:
            with open(filename, "wb") as fp:
                self.ftp.cwd( d )
                res = self.ftp.retrbinary("RETR " + filename, fp.write)
                if not res.startswith('226 Transfer complete'):
                    return res
            fp.close()
        except ftplib.all_errors as e:
            raise e
        if not self.persist:
            self.ftp.close()
        return True

    def delete_all(self, d = '/pp'):
        try:

            self.ftp.cwd( '.' )

            files = list( self.ftp.nlst( d ) )
            for f in files:
                self.ftp.delete( f )
        except ftplib.all_errors as e:
            raise e
        if not self.persist:
            self.ftp.close()

    def delete(self, f):
        try:

            self.ftp.cwd( '.' )

            self.ftp.delete( f )
        except ftplib.all_errors as e:
            raise e
        if not self.persist:
            self.ftp.close()
    def kill( self ):
        self.ftp.close()