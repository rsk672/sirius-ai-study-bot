class Name:
    def __init__(self, d):
        self.d = d
    
    def __getitem__(self, s):
        if type(s) == tuple:
            args = s[1:]
            s = s[0]
            if s in self.d:
                return self.d[s].format(*args)
            return s
        if s in self.d:
            return self.d[s]
        return s
        
    def add(self, x, y):
        self.d[x] = y
        
    def __contains__(self, x):
        return x in self.d
    
    def __delitem__(self, x):
        del self.d[x]
        
    def safe_delete(self, x):
        if x in self.d:
            del self.d[x]
    
    def pop(self, x, default = None):
        return self.d.pop(x, default)
    
    def clear(self):
        self.d.clear()
    
