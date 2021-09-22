from des import SchedulerDES
from event import Event, EventTypes
from process import ProcessStates

# gets the next ready process
def get_ready(processes):
    # get list of ready processes, then get first process
    return [p for p in processes if p.process_state == ProcessStates.READY].pop(0);


# First come, first serve
class FCFS(SchedulerDES):
    
    def scheduler_func(self, cur_event):
        return get_ready(self.processes) # get the first ready process
    
    def dispatcher_func(self, cur_process):
        cur_process.process_state = ProcessStates.RUNNING # set the process state to running
        process_ran_for = cur_process.run_for(cur_process.remaining_time, self.time) # run it for its remaining time
        cur_process.process_state = ProcessStates.TERMINATED # set its state to terminated
        return Event(process_id=cur_process._process_id, event_type=EventTypes.PROC_CPU_DONE,
                     event_time=self.time + process_ran_for) # return a new done event for this proccess


# Shortest Job First
class SJF(SchedulerDES):
    
    def scheduler_func(self, cur_event):
        """
        get a sorted list of the processes based on the service time
        passes to the get_ready function
        so we get the first ready process with least service time
        """
        return get_ready(sorted(self.processes, key=lambda process: process.service_time))

    def dispatcher_func(self, cur_process):
        # set process state to running
        cur_process.process_state = ProcessStates.RUNNING 
        # run it for its service time, should the be shortest time
        process_ran_for = cur_process.run_for(cur_process._service_time, self.time) 
        # set its state to terminated
        cur_process.process_state = ProcessStates.TERMINATED 
        # return done event for this process
        return Event(process_id=cur_process._process_id, event_type=EventTypes.PROC_CPU_DONE,
                     event_time=self.time + process_ran_for) 

# Round Robin
class RR(SchedulerDES):
    
    def scheduler_func(self, cur_event):
        # get the first ready process
        return get_ready(self.processes) 

    def dispatcher_func(self, cur_process):
        # set state to running
        cur_process.process_state = ProcessStates.RUNNING 
        # run it for quantum
        process_ran_for = cur_process.run_for(self.quantum, self.time) 
        # if its not done
        if cur_process.remaining_time > 0: 
             # make it ready again
            cur_process.process_state = ProcessStates.READY
            
            """
            we want to put this process now in the end of the processes list..
            but if we insert the process at end, then it will be behind of some processes which didn't arrive yet
            
            assume [P1=ready, P2=ready, P3=new, P4=new] 
            
            where P1, P2, P3 represent processes with some states
            assume P3 turns into ready after P1 is executed, but P4 still new
            since P4 is new, when we finish servicing P1, if we put it at end, we may have
            
            [P2=ready, P3=ready, P4=new, P1=ready] 

            since P4 may still be new, meaning it didn't arrive yet (since __update_process_states in des.py)
            this means we have a ready process scheduled to run after a process that didn't arrive.. thats not good.

            so its only logical to put P1, when its done and has remaining time after the last ready process which is in this case P3
            so we would have after running P1 for the first time
            [P2=ready, P3=ready, P1=ready, P4=new] 
            then running P2 
            [P3=ready, P1=ready, P2=ready, P4=new] 
            until P4 arrives
            [P1=ready, P2=ready, P4=ready, P3=ready] 

            i hope that makes sense
            """
            # remove it to re add it
            self.processes.remove(cur_process)
            # it should be added after all the processes that are not new, so by getting length of not new processes
            # we can find index where to put it
            # this is equivelant to adding one to the endex for every process that is ready or terminated
            index = len([p for p in self.processes if p.process_state != ProcessStates.NEW])
            # the index we currently have assumes no new events arrived when process executed, but this may not be true
            # lets find a list of newly arrived events and add the index to it since these events would be new processes changing state
            # this could have been done in a shorter way.. 
            for event in self.events_queue:
                if event.event_time > self.time and event.event_time < (self.time + process_ran_for):
                    index = index+1
            # insert it in the index
            self.processes.insert(index, cur_process)
            # return request access to event to show process still needs future access
            return Event(process_id=cur_process._process_id, event_type=EventTypes.PROC_CPU_REQ,
                         event_time=self.time+process_ran_for) 
        # if its done, set state to terminated
        cur_process.process_state = ProcessStates.TERMINATED 
        # return a done event
        return Event(process_id=cur_process._process_id, event_type=EventTypes.PROC_CPU_DONE,
                         event_time=self.time+process_ran_for) 

# Shortest remaining time first
class SRTF(SchedulerDES):
    
    def scheduler_func(self, cur_event):
        """
        get a sorted list of the processes based on the remaining time
        passes to the get_ready function
        so we get the first ready process with least remaining time
        """
        return get_ready(sorted(self.processes, key=lambda process: process.remaining_time))

    def dispatcher_func(self, cur_process):
        # set process state to running
        cur_process.process_state = ProcessStates.RUNNING 
        """
        Runs until the next event comes
        next_event_time should return time of next event
        we subtract it from the current time to know how long the process should run
        """
        process_ran_for = cur_process.run_for(self.next_event_time()-self.time, self.time) 
        # if its not done
        if cur_process.remaining_time != 0: 
            # make it ready again
            cur_process.process_state = ProcessStates.READY 
            # return request access to event to show process still needs future access
            return Event(process_id=cur_process._process_id, event_type=EventTypes.PROC_CPU_REQ,
                         event_time=self.time+process_ran_for) 
        # if it is done, it wouldn't have returned above, so code continues, so terminate
        cur_process.process_state = ProcessStates.TERMINATED 
        # return a done event
        return Event(process_id=cur_process._process_id, event_type=EventTypes.PROC_CPU_DONE,
                         event_time=self.time+process_ran_for)
