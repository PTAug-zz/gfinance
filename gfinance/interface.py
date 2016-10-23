class FinanceResults:
    """
    This class defines a Finance Results object. It contains the data
    of Google Finance on a given date.
    
    This object should never be instantiated directly by the user. The 
    class FinanceDatabase takes care of that. To get the FinanceResults
    object of a date, one should use the get_results_from_date method
    of the FinanceDatabase object.
    """
    
    def __init__(self,settings,date_of_data:str):
        """
        Constructor of the object. The settings argument is a 
        dictionary containing db and collection.
        The constructor fetches the report in the MongoDB database.
        The object has two attributes: the data and the date
        """
        self._settings = settings
        self._collection = MongoClient()[self._settings["db"]][self._settings["collection"]]
        dbFinance = self._collection.find_one({"date":date_of_data})
        self.data = dbFinance['data']
        self.date = dbFinance['date']
    
    def get_data(self):
        return self.data
    
    def get_date(self):
        return self.date
    
    def greatest_move_sector(self):
        """
        This function returns the name of the stock that has the
        greatest move for the day, positively or negatively. Note
        that it doesn't return the change value, just the name.
        """
        val=None
        maxx = max([abs(sec['change']) for sec in self.data.values()])
        for x,y in self.data.items():
            if abs(y['change'])==maxx:
                return x
            
    def greatest_move_stock(self):
        """
        This function returns the name of the stock that has the
        greatest move for the day, positively or negatively. Note
        that it doesn't return the change value, just the name.
        """
        max_move=''
        max_move_value=0
        for sec in self.data.values():
            if sec['biggest_gainer']['change'] is not None and abs(sec['biggest_gainer']['change'])>abs(max_move_value):
                max_move_value=sec['biggest_gainer']['change']
                max_move=sec['biggest_gainer']['equity']
            if sec['biggest_loser']['change'] is not None and abs(sec['biggest_loser']['change'])>abs(max_move_value):
                max_move_value=sec['biggest_loser']['change']
                max_move=sec['biggest_loser']['equity']
        return max_move
            
    def change_sector(self,sector:str):
        """
        This function returns the change for the given sector. If the sector
        does not exist, it raises a ValueError.
        """
        if sector in self.data:
            return self.data[sector]['change']
        else:
            raise ValueError("The sector does not exist")
            
    def change_stock(self,stock):
        """
        This function returns the change for the given stock. If the stock
        is not in the daily report, it raises a ValueError.
        """
        for sec in self.data.values():
            if sec['biggest_gainer']['equity'] is not None and sec['biggest_gainer']['equity']==stock:
                return sec['biggest_gainer']['change']
            if sec['biggest_loser']['equity'] is not None and sec['biggest_loser']['equity']==stock:
                return sec['biggest_loser']['change']
        else:
            raise ValueError("The stock is not in the daily report")
    
    def average_market_move(self):
        """
        This function returns the average market move, i.e. the mean
        of all sector changes.
        """
        list_sec_move = [sec['change'] for sec in self.data.values()]
        return np.mean(list_sec_move)
    
    def sector_rel_perf(self,sec1:str,sec2:str):
        """
        This function returns the relative performance of sector sec1 
        relatively to sector sec2, in %.
        """
        rel_perf = self.change_sector(sec1) - self.change_sector(sec2)
        return rel_perf
    
    def plot_market_move(self):
        """
        This function plots the average market move of the day.
        """
        sector_names = [sec for sec in self.data]
        sector_moves = [self.change_sector(sec) for sec in sector_names]
        colors=[{-1:'#E8755B',1:'#349454'}.get(np.sign(mov),'r') for mov in sector_moves]

        x=range(len(sector_moves))
        plt.xticks(x,sector_names,rotation=90)
        plt.bar(x, sector_moves,align="center",color=colors,width=1,edgecolor='white')
        plt.ylabel('Average Market Move (in %) on '+self.date)
        plt.show()

class FinanceDatabase:
    """
    This class defines a Finance Results object. It contains a list
    of FinanceReport objects.
    
    This object is what should be used by the user. To get a FinanceReport
    object associated with a date, one should use the get_results_from_date
    function.
    """
    def __init__(self,db:str,collection:str):
        """
        This constructor calls the FinanceResults constructor for each date
        found in the database.
        """
        self._settings = {"db":db,"collection":collection}
        self._collection = MongoClient()[self._settings["db"]][self._settings["collection"]]
        self.dates=[c['date'] for c in self._collection.find()]
        self.list_results=[FinanceResults(self._settings,c) for c in self.dates]
    
    def update_db(self):
        """
        This function updates the MongoDB database and the FinanceDatabase object.
        It uses the function google_sector_report(). 
        Each report is stored in a new file in the collection. This design works
        well for the functions we created and for how we created our FinanceDatabase
        object.
        
        If there's not entry for the present day, it is created and put in the database.
        If there's already an entry for the present day, the existing entry is deleted
        and the data is reloaded from Google Finance.
        """
        try:
            data=google_sector_report()
            import json
            today_date=date.today().isoformat()
            new_entry={'date': today_date,'data':json.loads(data)["result"]}
            if self._collection.count({'date':{'$eq':date.today().isoformat()}}) > 0:
                self._collection.delete_one({'date':{'$eq':date.today().isoformat()}})
            self._collection.insert_one(new_entry)
            self.dates.append(today_date)
            self.list_results.append(FinanceResults(self._settings,today_date))
        except Exception as err:
            print('Problem with the update.')
            raise
        return True
    
    def dates(self):
        return self.dates
    
    def list_results(self):
        return self.list_results
    
    def get_results_from_date(self,date:str):
        """
        This function returns the FinanceResults object of the input date.
        The date should be formatted as : '2016-10-17'.
        
        This function should be used if the user wants to get a FinanceResults
        object to apply analysis functions on.
        """
        if date in self.dates:
            return self.list_results[self.dates.index(date)]
        else:
            print("There is no report at the input date")
            return None
    
    def greatest_sector_move_ever(self):
        """
        This function returns the greatest sector move of all times.
        It only returns the name of the sector.
        """
        from operator import itemgetter
        list_max_sector=[(res.date,res.greatest_move_sector(),res.change_sector(res.greatest_move_sector())) 
                         for res in self.list_results]
        return max(list_max_sector,key=itemgetter(2))
    
    def greatest_stock_move_ever(self):
        """
        This function returns the greatest stock move of all times.
        It only returns the name of the stock.
        """
        from operator import itemgetter
        list_max_stock=[(res.date,res.greatest_move_stock(),res.change_stock(res.greatest_move_stock())) 
                         for res in self.list_results]
        return max(list_max_stock,key=itemgetter(2))
    
    def sector_changes(self,sector:str):
        """
        This function returns a list of tuples (date, change) for
        the given sector.
        """
        return [(res.date,res.change_sector(sector)) for res in self.list_results] 
    
    def average_sector_move(self,sector:str):
        """
        This function the average sector move of the sector, on
        all times.
        """     
        dates,changes=zip(*self.sector_changes(sector))
        return np.mean(changes)
    
    def plot_sector_changes(self,sector):
        """
        This function plots the changes of a sector on each day.
        """
        my_xticks,y=[list(a) for a in zip(*self.sector_changes(sector))]
        x=range(len(my_xticks))
        print(x,my_xticks)
        plt.xticks(x,my_xticks,rotation=45)
        plt.ylabel('Average '+sector+' move (in %)')
        plt.plot(x,y)
        plt.show()
        
    def plot_average_sector_move_all_times(self):
        """
        This function plots the average move of sectors during all times.
        """        
        sector_names = [sec for sec in self.list_results[0].data]
        sector_moves = [self.average_sector_move(sec) for sec in sector_names]
        colors=[{-1:'#E8755B',1:'#349454'}.get(np.sign(mov),'r') for mov in sector_moves]

        x=range(len(sector_moves))
        plt.xticks(x,sector_names,rotation=90)
        plt.bar(x, sector_moves,align="center",color=colors,width=1,edgecolor='white')
        plt.ylabel('Average Sector Move (in %)')
        plt.show()