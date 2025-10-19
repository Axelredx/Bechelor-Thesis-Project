import time

class TimeEstimator:
    def __init__(self):
        self.__start_time = None
        # for an operation we consider the whole pocess of reading, evaluating by claude and moving the file
        self.total_operations = 0

    '''start timer'''
    def start_counting_time(self) -> None:
        self.__start_time = time.time()

    '''stop timer'''
    def __stop_counting_time(self) -> float:
        if self.__start_time is None:
            raise ValueError("Timer has not been started. Call start_counting_time() first.\n")
        elapsed_time = time.time() - self.__start_time
        self.__start_time = None
        return elapsed_time
    
    '''print total time passed & operations executed'''
    def estimate_total_time_and_op(self) -> None:
        total_time = self.__stop_counting_time()
        if self.total_operations == 0:
            return
        tmp_op = self.total_operations
        self.total_operations = 0
        return total_time, total_time / tmp_op