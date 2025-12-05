package speech

import (
	"sync"
	"time"
)

// Job beschreibt einen STT-Job.
type Job struct {
	ID         string
	AudioB64   string
	SampleRate int
	Channels   int
	CreatedAt  time.Time
}

// Queue verwaltet STT-Jobs.
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
	q.cond.Signal()
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
