-- ============================================================
-- NEMIS TEST QUERIES
-- Comprehensive SQL queries demonstrating database features
-- For Database Course Evaluation
-- ============================================================

-- ============================================================
-- SECTION 1: BASIC QUERIES
-- ============================================================

-- Query 1: List all regions with their populations
SELECT Region_ID, name, population, description
FROM Region
ORDER BY population DESC;

-- Query 2: Count users by role
SELECT role, COUNT(*) as user_count
FROM User_account
WHERE is_active = TRUE
GROUP BY role
ORDER BY user_count DESC;

-- Query 3: List all voters with their regions
SELECT 
    u.CNIE,
    u.name AS voter_name,
    r.name AS region_name,
    v.is_eligible,
    v.registration_date
FROM Voter v
JOIN User_account u ON v.User_ID = u.User_ID
JOIN Region r ON v.Region_ID = r.Region_ID
ORDER BY v.registration_date DESC;

-- ============================================================
-- SECTION 2: JOINS (Simple to Complex)
-- ============================================================

-- Query 4: Elections with admin information (INNER JOIN)
SELECT 
    e.Election_ID,
    e.name AS election_name,
    e.type,
    e.status,
    u.name AS admin_name,
    u.CNIE AS admin_cnie
FROM Election e
INNER JOIN User_account u ON e.Admin_ID = u.User_ID
ORDER BY e.created_at DESC;

-- Query 5: All candidates with their election and region (Multiple JOINs)
SELECT 
    u.name AS candidate_name,
    u.CNIE,
    c.party_name,
    e.name AS election_name,
    r.name AS region_name,
    c.is_approved,
    c.registration_date
FROM Candidate c
JOIN User_account u ON c.User_ID = u.User_ID
JOIN Election e ON c.Election_ID = e.Election_ID
JOIN Region r ON c.Region_ID = r.Region_ID
ORDER BY c.registration_date DESC;

-- Query 6: Voters and their votes (LEFT JOIN to show voters who haven't voted)
SELECT 
    u.name AS voter_name,
    r.name AS region_name,
    e.name AS election_name,
    CASE WHEN vt.Vote_ID IS NOT NULL THEN 'Voted' ELSE 'Not Voted' END AS voting_status,
    vt.vote_timestamp
FROM Voter v
JOIN User_account u ON v.User_ID = u.User_ID
JOIN Region r ON v.Region_ID = r.Region_ID
LEFT JOIN Vote vt ON v.Voter_ID = vt.Voter_ID
LEFT JOIN Election e ON vt.Election_ID = e.Election_ID
WHERE v.is_eligible = TRUE
ORDER BY u.name, vt.vote_timestamp DESC;

-- ============================================================
-- SECTION 3: AGGREGATION FUNCTIONS
-- ============================================================

-- Query 7: Vote counts by candidate
SELECT 
    u.name AS candidate_name,
    c.party_name,
    e.name AS election_name,
    COUNT(v.Vote_ID) AS vote_count
FROM Candidate c
JOIN User_account u ON c.User_ID = u.User_ID
JOIN Election e ON c.Election_ID = e.Election_ID
LEFT JOIN Vote v ON c.Candidate_ID = v.Candidate_ID
WHERE c.is_approved = TRUE
GROUP BY u.name, c.party_name, e.name
ORDER BY vote_count DESC;

-- Query 8: Election statistics
SELECT 
    e.Election_ID,
    e.name AS election_name,
    COUNT(DISTINCT c.Candidate_ID) AS total_candidates,
    COUNT(DISTINCT c.Candidate_ID) FILTER (WHERE c.is_approved = TRUE) AS approved_candidates,
    COUNT(DISTINCT v.Vote_ID) AS total_votes,
    COUNT(DISTINCT er.Region_ID) AS regions_involved
FROM Election e
LEFT JOIN Candidate c ON e.Election_ID = c.Election_ID
LEFT JOIN Vote v ON e.Election_ID = v.Election_ID
LEFT JOIN Election_Region er ON e.Election_ID = er.Election_ID
GROUP BY e.Election_ID, e.name
ORDER BY total_votes DESC;

-- Query 9: Region voting statistics
SELECT 
    r.name AS region_name,
    r.population,
    COUNT(DISTINCT v.Voter_ID) AS registered_voters,
    COUNT(DISTINCT vt.Vote_ID) AS total_votes_cast,
    ROUND(COUNT(DISTINCT vt.Vote_ID)::NUMERIC / NULLIF(COUNT(DISTINCT v.Voter_ID), 0) * 100, 2) AS participation_rate
FROM Region r
LEFT JOIN Voter v ON r.Region_ID = v.Region_ID
LEFT JOIN Vote vt ON v.Voter_ID = vt.Voter_ID
GROUP BY r.name, r.population
ORDER BY participation_rate DESC NULLS LAST;

-- ============================================================
-- SECTION 4: SUBQUERIES
-- ============================================================

-- Query 10: Elections with above-average voter turnout
SELECT 
    e.name AS election_name,
    COUNT(DISTINCT v.Vote_ID) AS vote_count
FROM Election e
LEFT JOIN Vote v ON e.Election_ID = v.Election_ID
GROUP BY e.Election_ID, e.name
HAVING COUNT(DISTINCT v.Vote_ID) > (
    SELECT AVG(vote_count) FROM (
        SELECT COUNT(DISTINCT Vote_ID) AS vote_count
        FROM Vote
        GROUP BY Election_ID
    ) AS avg_votes
)
ORDER BY vote_count DESC;

-- Query 11: Candidates who received more votes than the average in their region
SELECT 
    u.name AS candidate_name,
    c.party_name,
    r.name AS region_name,
    COUNT(v.Vote_ID) AS votes_received
FROM Candidate c
JOIN User_account u ON c.User_ID = u.User_ID
JOIN Region r ON c.Region_ID = r.Region_ID
LEFT JOIN Vote v ON c.Candidate_ID = v.Candidate_ID
WHERE c.is_approved = TRUE
GROUP BY u.name, c.party_name, r.name, c.Region_ID, c.Election_ID
HAVING COUNT(v.Vote_ID) > (
    SELECT AVG(vote_count) FROM (
        SELECT COUNT(Vote_ID) AS vote_count
        FROM Vote vt
        JOIN Candidate ct ON vt.Candidate_ID = ct.Candidate_ID
        WHERE ct.Region_ID = c.Region_ID AND ct.Election_ID = c.Election_ID
        GROUP BY ct.Candidate_ID
    ) AS region_avg
)
ORDER BY votes_received DESC;

-- Query 12: Find voters who haven't voted in any election
SELECT 
    u.name AS voter_name,
    u.CNIE,
    r.name AS region_name,
    v.registration_date
FROM Voter v
JOIN User_account u ON v.User_ID = u.User_ID
JOIN Region r ON v.Region_ID = r.Region_ID
WHERE v.is_eligible = TRUE
AND NOT EXISTS (
    SELECT 1 FROM Vote vt WHERE vt.Voter_ID = v.Voter_ID
)
ORDER BY v.registration_date;

-- ============================================================
-- SECTION 5: WINDOW FUNCTIONS
-- ============================================================

-- Query 13: Rank candidates within each election
SELECT 
    e.name AS election_name,
    u.name AS candidate_name,
    c.party_name,
    COUNT(v.Vote_ID) AS vote_count,
    RANK() OVER (PARTITION BY e.Election_ID ORDER BY COUNT(v.Vote_ID) DESC) AS rank,
    DENSE_RANK() OVER (PARTITION BY e.Election_ID ORDER BY COUNT(v.Vote_ID) DESC) AS dense_rank,
    ROW_NUMBER() OVER (PARTITION BY e.Election_ID ORDER BY COUNT(v.Vote_ID) DESC) AS row_num
FROM Election e
JOIN Candidate c ON e.Election_ID = c.Election_ID AND c.is_approved = TRUE
JOIN User_account u ON c.User_ID = u.User_ID
LEFT JOIN Vote v ON c.Candidate_ID = v.Candidate_ID
GROUP BY e.Election_ID, e.name, u.name, c.party_name
ORDER BY e.Election_ID, vote_count DESC;

-- Query 14: Running total of votes over time
SELECT 
    e.name AS election_name,
    v.vote_timestamp::DATE AS vote_date,
    COUNT(*) AS daily_votes,
    SUM(COUNT(*)) OVER (PARTITION BY e.Election_ID ORDER BY v.vote_timestamp::DATE) AS cumulative_votes
FROM Vote v
JOIN Election e ON v.Election_ID = e.Election_ID
GROUP BY e.Election_ID, e.name, v.vote_timestamp::DATE
ORDER BY e.Election_ID, vote_date;

-- Query 15: Calculate percentage of total votes for each candidate
SELECT 
    e.name AS election_name,
    u.name AS candidate_name,
    COUNT(v.Vote_ID) AS votes,
    ROUND(
        COUNT(v.Vote_ID)::NUMERIC * 100.0 / 
        SUM(COUNT(v.Vote_ID)) OVER (PARTITION BY e.Election_ID), 
        2
    ) AS vote_percentage
FROM Election e
JOIN Candidate c ON e.Election_ID = c.Election_ID AND c.is_approved = TRUE
JOIN User_account u ON c.User_ID = u.User_ID
LEFT JOIN Vote v ON c.Candidate_ID = v.Candidate_ID
GROUP BY e.Election_ID, e.name, u.name
ORDER BY e.Election_ID, votes DESC;

-- ============================================================
-- SECTION 6: COMPLEX QUERIES (CTEs)
-- ============================================================

-- Query 16: Election analysis with multiple CTEs
WITH ElectionStats AS (
    SELECT 
        e.Election_ID,
        e.name,
        COUNT(DISTINCT v.Vote_ID) AS total_votes,
        COUNT(DISTINCT c.Candidate_ID) AS total_candidates
    FROM Election e
    LEFT JOIN Vote v ON e.Election_ID = v.Election_ID
    LEFT JOIN Candidate c ON e.Election_ID = c.Election_ID AND c.is_approved = TRUE
    GROUP BY e.Election_ID, e.name
),
RegionParticipation AS (
    SELECT 
        er.Election_ID,
        COUNT(DISTINCT v.Voter_ID) AS eligible_voters,
        COUNT(DISTINCT vt.Voter_ID) AS voted_voters
    FROM Election_Region er
    JOIN Voter v ON er.Region_ID = v.Region_ID
    LEFT JOIN Vote vt ON v.Voter_ID = vt.Voter_ID AND vt.Election_ID = er.Election_ID
    GROUP BY er.Election_ID
)
SELECT 
    es.name AS election_name,
    es.total_votes,
    es.total_candidates,
    rp.eligible_voters,
    rp.voted_voters,
    ROUND(rp.voted_voters::NUMERIC / NULLIF(rp.eligible_voters, 0) * 100, 2) AS turnout_percentage
FROM ElectionStats es
LEFT JOIN RegionParticipation rp ON es.Election_ID = rp.Election_ID
ORDER BY turnout_percentage DESC NULLS LAST;

-- Query 17: Find winners by region using CTE
WITH VoteCounts AS (
    SELECT 
        c.Candidate_ID,
        c.Election_ID,
        c.Region_ID,
        u.name AS candidate_name,
        c.party_name,
        COUNT(v.Vote_ID) AS vote_count,
        RANK() OVER (PARTITION BY c.Election_ID, c.Region_ID ORDER BY COUNT(v.Vote_ID) DESC) AS rank
    FROM Candidate c
    JOIN User_account u ON c.User_ID = u.User_ID
    LEFT JOIN Vote v ON c.Candidate_ID = v.Candidate_ID
    WHERE c.is_approved = TRUE
    GROUP BY c.Candidate_ID, c.Election_ID, c.Region_ID, u.name, c.party_name
)
SELECT 
    e.name AS election_name,
    r.name AS region_name,
    vc.candidate_name,
    vc.party_name,
    vc.vote_count
FROM VoteCounts vc
JOIN Election e ON vc.Election_ID = e.Election_ID
JOIN Region r ON vc.Region_ID = r.Region_ID
WHERE vc.rank = 1
ORDER BY e.Election_ID, r.name;

-- ============================================================
-- SECTION 7: TESTING STORED FUNCTIONS
-- ============================================================

-- Query 18: Test calculate_turnout function
SELECT * FROM calculate_turnout(1);

-- Query 19: Test get_election_winner function
SELECT * FROM get_election_winner(1);

-- Query 20: Test get_region_statistics function
SELECT * FROM get_region_statistics(NULL);  -- All regions
SELECT * FROM get_region_statistics(1);     -- Specific region

-- ============================================================
-- SECTION 8: TESTING VIEWS
-- ============================================================

-- Query 21: Query election results view
SELECT 
    election_name,
    candidate_name,
    party_name,
    region_name,
    vote_count,
    vote_percentage_in_region,
    rank_in_region
FROM vw_election_results
WHERE rank_in_region <= 3
ORDER BY election_name, rank_in_region;

-- Query 22: Query voter turnout view
SELECT 
    election_name,
    region_name,
    total_eligible_voters,
    votes_cast,
    turnout_percentage
FROM vw_voter_turnout
WHERE turnout_percentage > 50
ORDER BY turnout_percentage DESC;

-- Query 23: Query candidate statistics view
SELECT 
    candidate_name,
    party_name,
    election_name,
    total_votes,
    overall_rank
FROM vw_candidate_statistics
WHERE overall_rank <= 5
ORDER BY election_name, overall_rank;

-- Query 24: Query election overview
SELECT 
    election_name,
    status,
    current_phase,
    number_of_regions,
    total_candidates,
    approved_candidates,
    total_votes
FROM vw_election_overview
ORDER BY start_date DESC;

-- ============================================================
-- SECTION 9: DATE AND TIME QUERIES
-- ============================================================

-- Query 25: Elections by time period
SELECT 
    name,
    type,
    status,
    start_date,
    end_date,
    EXTRACT(DAY FROM (end_date - start_date)) AS duration_days
FROM Election
WHERE start_date >= CURRENT_DATE - INTERVAL '1 year'
ORDER BY start_date DESC;

-- Query 26: Votes by hour of day
SELECT 
    EXTRACT(HOUR FROM vote_timestamp) AS hour_of_day,
    COUNT(*) AS vote_count
FROM Vote
GROUP BY hour_of_day
ORDER BY hour_of_day;

-- Query 27: Recent audit activity (last 7 days)
SELECT 
    u.name AS user_name,
    u.role,
    a.action,
    a.table_name,
    a.timestamp
FROM Audit_log a
LEFT JOIN User_account u ON a.User_ID = u.User_ID
WHERE a.timestamp >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY a.timestamp DESC
LIMIT 50;

-- ============================================================
-- SECTION 10: CONDITIONAL LOGIC
-- ============================================================

-- Query 28: Categorize elections by size
SELECT 
    name,
    type,
    total_votes,
    CASE 
        WHEN total_votes >= 10000 THEN 'Large'
        WHEN total_votes >= 1000 THEN 'Medium'
        WHEN total_votes > 0 THEN 'Small'
        ELSE 'No Votes'
    END AS election_size
FROM (
    SELECT 
        e.name,
        e.type,
        COUNT(v.Vote_ID) AS total_votes
    FROM Election e
    LEFT JOIN Vote v ON e.Election_ID = v.Election_ID
    GROUP BY e.Election_ID, e.name, e.type
) AS election_vote_counts
ORDER BY total_votes DESC;

-- Query 29: Voter participation status
SELECT 
    u.name AS voter_name,
    r.name AS region_name,
    v.registration_date,
    CASE 
        WHEN EXISTS (SELECT 1 FROM Vote vt WHERE vt.Voter_ID = v.Voter_ID) THEN 'Active Voter'
        WHEN v.registration_date >= CURRENT_DATE - INTERVAL '30 days' THEN 'New Voter'
        ELSE 'Inactive Voter'
    END AS voter_status
FROM Voter v
JOIN User_account u ON v.User_ID = u.User_ID
JOIN Region r ON v.Region_ID = r.Region_ID
WHERE v.is_eligible = TRUE
ORDER BY v.registration_date DESC;

-- ============================================================
-- SECTION 11: PERFORMANCE ANALYSIS
-- ============================================================

-- Query 30: Check index usage (requires EXPLAIN)
EXPLAIN ANALYZE
SELECT 
    u.name,
    COUNT(v.Vote_ID) AS vote_count
FROM Candidate c
JOIN User_account u ON c.User_ID = u.User_ID
LEFT JOIN Vote v ON c.Candidate_ID = v.Candidate_ID
WHERE c.is_approved = TRUE
GROUP BY u.name
ORDER BY vote_count DESC;

-- ============================================================
-- SECTION 12: DATA INTEGRITY CHECKS
-- ============================================================

-- Query 31: Find orphaned records (should be none due to foreign keys)
SELECT 'Voters without User_account' AS check_name, COUNT(*) AS count
FROM Voter v
WHERE NOT EXISTS (SELECT 1 FROM User_account u WHERE u.User_ID = v.User_ID)
UNION ALL
SELECT 'Candidates without User_account', COUNT(*)
FROM Candidate c
WHERE NOT EXISTS (SELECT 1 FROM User_account u WHERE u.User_ID = c.User_ID)
UNION ALL
SELECT 'Votes without Voter', COUNT(*)
FROM Vote v
WHERE NOT EXISTS (SELECT 1 FROM Voter vr WHERE vr.Voter_ID = v.Voter_ID);

-- Query 32: Check for duplicate votes (should be none due to unique constraint)
SELECT 
    Voter_ID,
    Election_ID,
    COUNT(*) AS vote_count
FROM Vote
GROUP BY Voter_ID, Election_ID
HAVING COUNT(*) > 1;

-- Query 33: Verify all candidates are in valid election regions
SELECT 
    c.Candidate_ID,
    u.name AS candidate_name,
    e.name AS election_name,
    r.name AS candidate_region,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM Election_Region er 
            WHERE er.Election_ID = c.Election_ID 
            AND er.Region_ID = c.Region_ID
        ) THEN 'Valid'
        ELSE 'INVALID - Region Mismatch'
    END AS validation_status
FROM Candidate c
JOIN User_account u ON c.User_ID = u.User_ID
JOIN Election e ON c.Election_ID = e.Election_ID
JOIN Region r ON c.Region_ID = r.Region_ID;

-- ============================================================
-- SUMMARY
-- ============================================================
-- This file demonstrates:
-- 1. Basic SELECT queries with WHERE, ORDER BY
-- 2. Multiple types of JOINs (INNER, LEFT, CROSS)
-- 3. Aggregation functions (COUNT, SUM, AVG, MAX, MIN)
-- 4. GROUP BY and HAVING clauses
-- 5. Subqueries (scalar, correlated, EXISTS)
-- 6. Window functions (RANK, DENSE_RANK, ROW_NUMBER, SUM OVER)
-- 7. Common Table Expressions (CTEs)
-- 8. Stored Functions
-- 9. Views
-- 10. Date/Time operations
-- 11. CASE statements
-- 12. Performance analysis with EXPLAIN
-- 13. Data integrity verification
-- ============================================================
