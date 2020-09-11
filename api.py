from db.mysql import Connection
import sys, os
import json

N_SETTINGS = 2


def fetchName( uid ):
    return Connection().get( f"SELECT * FROM `users` WHERE id={uid}" )[0][1]

class FriendRequest:
    def __init__( self, _id, uid ):
        self.uid = uid
        self._id = _id
        self.db = Connection()
    @staticmethod
    def send( uid, tpuid ):
        db = Connection()
        sql_0 = f"""SELECT * FROM `friends` WHERE (`uid`={uid} AND `tpuid`={tpuid})
                    OR (`uid`={tpuid} AND `tpuid`={uid}) AND flag=0"""
        sql_1 = f"""SELECT * FROM `friends` WHERE (`uid`={uid} AND `tpuid`={tpuid})
                    OR (`uid`={tpuid} AND `tpuid`={uid}) AND flag=1"""
        if ( db.check(sql_0) ):
            return -1
        elif ( db.check( sql_1 ) ):
            return -3
        sql = """
                    INSERT INTO `friends` (`uid`, `tpuid`)
                    VALUES
                    ( %s, %s )
              """ % ( uid, tpuid )
        return db.set( sql )
    @staticmethod
    def VsOb( uid, tpuid ):
        # friendship status check
        db = Connection()
        sql_0 = f"""SELECT * FROM `friends` WHERE ((`uid`={uid} AND `tpuid`={tpuid})
                    OR (`uid`={tpuid} AND `tpuid`={uid})) AND flag=0"""
        sql_1 = f"""SELECT * FROM `friends` WHERE ((`uid`={uid} AND `tpuid`={tpuid})
                    OR (`uid`={tpuid} AND `tpuid`={uid})) AND flag=1"""
        sql_2 = f"""SELECT * FROM `friends` WHERE (`uid`={uid} AND `tpuid`={tpuid}) AND flag=0"""
        sql_3 = f"""SELECT * FROM `friends` WHERE (`uid`={tpuid} AND `tpuid`={uid}) AND flag=0"""
        if ( db.check(sql_0) ):
            if ( db.check( sql_2 ) ):
                return -10
            else:
                return -11
            return -1
        elif ( db.check( sql_1 ) ):
            return -3
        return 0
    @staticmethod
    def fetch_requests(uid):
        db = Connection()
        sql = f"SELECT * FROM `friends` WHERE `tpuid`={uid} AND flag=0"
        res = db.get( sql )
        ret = []
        for i in res:
            ret.append( {
                'id': i[0],
                'uid': i[1],
                'tpuid': i[2],
                'sender': fetchName( i[1] ),
                'recv': fetchName( i[2] )
            } )
        return ret
    @staticmethod
    def is_accepted(uid, tpuid):
        db = Connection()
        sql = f"""SELECT * FROM `friends` WHERE ((`uid`={uid} AND `tpuid`={tpuid})
                 OR (`uid`={tpuid} AND `tpuid`={uid}))"""
        try:
            return db.get(sql)[-1][3] == 1
        except IndexError:
            return 501
    @staticmethod
    def fetch_id(uid, tpuid):
        db = Connection()
        sql = f"""SELECT * FROM `friends` WHERE ((`uid`={uid} AND `tpuid`={tpuid})
                 OR (`uid`={tpuid} AND `tpuid`={uid}))"""
        try:
            return db.get(sql)[-1][0]
        except IndexError:
            return None
    def accept( self ):
        sql = f"UPDATE `friends` SET `flag`=1 WHERE id={self._id} AND `tpuid`={self.uid}"
        return self.db.set( sql )
    def delete( self ):
        sql = f"DELETE FROM `friends` WHERE `id`={self._id} AND (`uid`={self.uid} OR `tpuid`={self.uid})"
        return self.db.set( sql )

def compute_neighbors(data, uid ):
    if ( type(data) == dict  ):
        dst = haversine( data, {'x': 0, 'y': 0} )
    else:
        dst = data
    update = f"UPDATE `users` SET dfe={dst} WHERE `id`={uid}"
    sql = f"SELECT * FROM `users` WHERE ( dfe>={dst}-2 AND dfe<={dst}+2 ) AND `id`!={uid}"
    db = Connection()
    if ( db.set( update ) ):
        res = db.get( sql )
        ret = []
        for i in res:
            ret.append({
                'tpuid': i[0],
                'name': i[1],
                'bio': i[4]
            })
        # print(ret, "nnin")
        return ret, dst
    return [], dst

class Friend(FriendRequest):
    @staticmethod
    def fetch_friends( uid ):
        db = Connection()
        sql = f"SELECT * FROM `friends` WHERE (`uid`={uid} OR `tpuid`={uid}) AND flag=1"
        res = db.get( sql )
        ret = []
        for i in res:
            if ( uid == i[1] ):
                ret.append( {
                    'id': i[0],
                    'uid': i[1],
                    'tpuid': i[2],
                    'prober': i[2],
                    'name': fetchName( i[2] )
                } )
            else:
                ret.append( {
                    'id': i[0],
                    'uid': i[1],
                    'prober': i[1],
                    'tpuid': i[2],
                    'name': fetchName( i[1] )
                } )
        return ret
    def block_friend( self ):
        sql = f"UPDATE `friends` SET flag=0 WHERE id={self._id} AND (`uid`={self.uid} OR `tpuid`={self.uid})"
        return self.db.set( sql )
    def unblock_friend( self ):
        sql = f"UPDATE `friends` SET flag=1 WHERE id={self._id} AND (`uid`={self.uid} OR `tpuid`={self.uid})"
        return self.db.set( sql )
    def unfriend( self ):
        return self.delete()

from math import pi, cos, sin, sqrt, atan2

def haversine(pos1, pos2):
    lat1 = float(pos1['x'])
    long1 = float(pos1['y'])
    lat2 = float(pos2['x'])
    long2 = float(pos2['y'])

    degree_to_rad = float(pi / 180.0)

    d_lat = (lat2 - lat1) * degree_to_rad
    d_long = (long2 - long1) * degree_to_rad

    a = pow(sin(d_lat / 2), 2) + cos(lat1 * degree_to_rad) * cos(lat2 * degree_to_rad) * pow(sin(d_long / 2), 2)
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    km = 6367 * c
    mi = 3956 * c
    return km

from datetime import datetime
import time
class Messenger:
    def __init__(self, uid):
        self.uid = uid
        self.db = Connection()
    def send_message( self, msg, tpuid, quoted = 0 ):
        msg = msg.replace('\\', '\\\\').replace('\"', '\\\"').replace( '\'', "\\\'" )
        # msg = json.dumps( msg )
        sql = """
                    INSERT INTO msg (`uid`, `tpuid`, `msg`, `quoted`, `date-sent`)
                    VALUES
                    (%s, %s, '%s', '%s', '%s')
              """ % ( self.uid, tpuid, msg, quoted, time.ctime() )
        return self.db.set( sql )
    def room_id( self, tpuid ):
        uid = self.uid
        sql = f"SELECT id FROM friends WHERE (tpuid={tpuid} OR `uid`={tpuid}) AND (`uid`={uid} OR tpuid={uid})"
        return self.db.get( sql )[0][0]
    def delete_message( self, _id ):
        sql = f"DELETE FROM msg WHERE id={_id} AND `uid`={self.uid}"
        return self.db.set( sql )
    def see( self, tpuid ):
        sql = f"UPDATE msg SET seen=1 WHERE `tpuid`={self.uid} AND `uid`={tpuid}"
        return self.db.set( sql )
    def seen( self, tpuid ):
        sql = f"SELECT * FROM msg WHERE `tpuid`={tpuid}"
        try:
            return self.db.get(sql)[-1][5] == 1
        except IndexError:
            return False
    def fetch_msg( self, tpuid, _id = 0, fil = 0 ):
        if ( tpuid != '*' ):
            sql = f"SELECT * FROM msg WHERE (`uid`={self.uid} AND `tpuid`={tpuid}) OR (`tpuid`={self.uid} AND `uid`={tpuid}) AND id>={_id}"
        else:
            sql = f"SELECT * FROM msg WHERE (`uid`={self.uid} OR `tpuid`={self.uid}) AND id>={_id}"
        res = self.db.get(sql)
        ret = []
        for i in res:
            filtered = i[3]

            offensive = json.load( open( "extras/offensive.json", "r" ) )

            for j in offensive:
                filtered = filtered.replace( j, offensive[j] )
                    
            ret.append( {
                'id': i[0],
                'uid': i[1],
                'msg': i[3],
                'filtered': filtered,
                'quoted': Messenger.id_probe( i[4] ),
                'seen': i[5] == 1,
                'date-sent': i[6]
            } )
        return ret
    @staticmethod
    def id_probe( _id ):
        sql = f"SELECT * FROM msg WHERE id={_id}"
        db = Connection()
        try:
            return db.get(sql)[0][3]
        except IndexError:
            return None

class Notifications:
    def __init__( self, uid ):
        self.uid = uid
        self.db = Connection()
    def send(self, msg, link):
        sql = """
                    INSERT INTO notifications ( `uid`, `msg`, `link` )
                    VALUES
                    ( %s, '%s', '%s' )
              """ % ( self.uid, msg, link )
        return self.db.set( sql )
    def fetch( self, spec = "*" ):
        sql = f"SELECT * FROM notifications WHERE `uid`={self.uid}"
        dat = self.db.get( sql )
        ret = []
        for i in dat:
            ret.append( {
                'id': i[0],
                'msg': i[2],
                'link': i[3],
                'seen': i[4],
                'datetime': i[5]
            } )
        return ret
    def see( self, _id ):
        sql = f"UPDATE notifications SET `seen`=1 WHERE `id`={_id} AND `uid`={self.uid}"
        return self.db.set( sql )
    @staticmethod
    def super_see( uid, link = "" ):
        db = Connection()
        sql = f"UPDATE notifications SET `seen`=1 WHERE `link`='{link}' AND `uid`={uid}"
        return db.set( sql )
    @staticmethod
    def super_pop( uid, link = "" ):
        db = Connection()
        sql = f"DELETE FROM notifications WHERE `link`='{link}' AND `uid`={uid}"
        return db.set( sql )

def is_online(uid, db):
    sql = f"SELECT * FROM `users` WHERE `id`={uid} AND active=1"
    return len(db.get( sql )) > 0

def load_settings(uid):
    name = f"{uid}.json"

    if ( name not in os.listdir("settings") ):

        json.dump( [0,0], open( f"settings/{name}", "w" ) )

        return [0,0]

    else:

        settings = json.load( open(f'settings/{name}', 'r') )

        return settings

# load_settings(1)

def change_settings(uid, ind, val = 1):
    name = f"{uid}.json"
    settings = load_settings(1)
    assert ind < len(settings), "Inputed index too large for zero indexed settings of size %s" % len(settings)

    settings[ind] = val

    json.dump( settings, open( f"settings/{name}", "w" ) )
    # json
    return settings

# change_settings(1, ind = 0, val = 0)    

# TODO: add toolbar for (messages[ copy, quote, delete ], notifications[delete])
# TODO: work on quoting messge feature
# fr = FriendRequest( _id = 2, uid = 3 )
# print( FriendRequest.send( 1, 4 ) )
# print( FriendRequest.fetch_requests( 3 ) )
# print( fr.accept( ) )

# f = Friend( _id = 2, uid = 1 )
# print( Friend.fetch_friends( 1 ) )
# print( f.block_friend() )
# print( f.unblock_friend() )

# m = Messenger( 3 )
# print( m.send_message( msg = "Bro I dey, U", tpuid = 1 ) )
# print( m.fetch_msg( 1 ) )
# print( m.see( 3 ) )
# print( m.seen( 3 ) )
# print( m.delete_message(1) )