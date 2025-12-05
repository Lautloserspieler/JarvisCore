package command

import (
	"sync"
	"time"
)

// Job beschreibt einen Command-Job.
type Job struct {
	ID        string
	Text      string
	Metadata  map[string]any
	Context   map[string]any
	Priority  int
	CreatedAt time.Time
}

// Queue verwaltet Jobs mit einfacher Priorisierung (höher = bevorzugt).
type Queue struct {
	mu    sync.Mutex
	cond  *sync.Cond
	jobs  []Job
	alive bool
}

func NewQueue() *Queue {
	q := &Queue{jobs: make([]Job, 0), alive: true}
	q.cond = sync.NewCond(&q.mu)
	return q
}

func (q *Queue) Enqueue(job Job) {
	q.mu.Lock()
	defer q.mu.Unlock()
	q.jobs = append(q.jobs, job)
	q.sort()
	q.cond.Signal()
}

func (q *Queue) sort() {
	// Simple insertion sort by priority desc, then FIFO
	for i := 1; i < len(q.jobs); i++ {
		j := i
		for j > 0 && q.jobs[j].Priority > q.jobs[j-1].Priority {
			q.jobs[j], q.jobs[j-1] = q.jobs[j-1], q.jobs[j]
			j--
		}
	}
}

func (q *Queue) Dequeue() (Job, bool) {
	q.mu.Lock()
	defer q.mu.Unlock()
	for len(q.jobs) == 0 && q.alive {
		q.cond.Wait()
	}
	if !q.alive {
		return Job{}, false
	}
	job := q.jobs[0]
	q.jobs = q.jobs[1:]
	return job, true
}

func (q *Queue) Close() {
	q.mu.Lock()
	defer q.mu.Unlock()
	q.alive = false
	q.cond.Broadcast()
}
