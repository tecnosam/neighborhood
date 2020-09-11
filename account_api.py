from db.mysql import Connection
import sys, os, hashlib

class User:
    def create( self, name, email, pwd ):
        pwd = hashlib.sha256( pwd.encode() ).hexdigest()
        sql = """
                    INSERT INTO users (name, email, pwd)
                    VALUES
                    ( '%s', '%s', '%s' )
            """ % (name, email, pwd)
        obj = Connection()
        return obj.set( sql )
    def login( self, email, pwd ):
        _pwd = hashlib.sha256( pwd.encode() ).hexdigest()
        sql = """
                    SELECT * FROM users WHERE email='%s' AND pwd='%s'
            """ % (email, _pwd)
        obj = Connection()
        if (obj.check( sql )):
            return obj.get( sql )[0]
        else:
            return False
        return db.set(sql)
    def ChangeAttr( self, node, val, uid ):
        if (node == 'pwd'):
            val = hashlib.sha256( val.encode() ).hexdigest()
        elif ( node in ['uid', 'mid', 'id'] ):
            return False
        if ( type( val ) == str ):
            val = val.replace('\\', '\\\\').replace('\"', '\\\"').replace( '\'', "\\\'" )
        sql = "UPDATE users SET `%s`='%s' WHERE id=%s" % ( node, val, uid )
        obj = Connection()
        return obj.set( sql )
    def ChangeMultiple( self, data, uid ):
        for i in data:
            try:
                self.ChangeAttr( i, data[ i ], uid )
            except:
                continue
        return True

def name(uid):
    db = Connection()
    sql = f"SELECT * FROM users WHERE id={uid}"
    return db.get( sql )[0][1] if db.check( sql ) == True else "Anonymous"

# gen_db = Connection()
def info(uid, adapter):
    sql = f"SELECT * FROM users WHERE id={uid}"
    return adapter.get( sql )[0] if adapter.check( sql ) == True else False


# obj = User()
# print( obj.create( "Catalina Jose", "cat@samabolo.com", "fish" ) )
# print( obj.login( "ikabolo59@gmail.com", "fish" ) )
# print( obj.login( "admin", "fish" ) )
# print( obj.ChangeAttr( 'bio', "Official neighborhood account of Abolo Samuel", 1 ) )