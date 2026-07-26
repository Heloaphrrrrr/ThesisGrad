--
-- PostgreSQL database dump
--

\restrict n20G6BbsIEzTZM7jHfbOUcAWZFAydch6efTbqbdPs38uLa3xDQGH0b8NN4oCEFd

-- Dumped from database version 18.3
-- Dumped by pg_dump version 18.3

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: cleaning_actions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cleaning_actions (
    action_id bigint NOT NULL,
    issue_id character varying(64),
    invoice_no character varying(32),
    table_name character varying(64) NOT NULL,
    column_name character varying(64) NOT NULL,
    old_value text,
    new_value text,
    action_type character varying(32) NOT NULL,
    action_status character varying(32) NOT NULL,
    action_by character varying(64) DEFAULT 'system'::character varying NOT NULL,
    action_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: cleaning_actions_action_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cleaning_actions_action_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cleaning_actions_action_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cleaning_actions_action_id_seq OWNED BY public.cleaning_actions.action_id;


--
-- Name: cleaning_runs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cleaning_runs (
    run_id bigint NOT NULL,
    run_mode character varying(32) NOT NULL,
    source_name character varying(255) NOT NULL,
    started_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    finished_at timestamp without time zone,
    status character varying(32) NOT NULL,
    notes text
);


--
-- Name: cleaning_runs_run_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cleaning_runs_run_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cleaning_runs_run_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cleaning_runs_run_id_seq OWNED BY public.cleaning_runs.run_id;


--
-- Name: customers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.customers (
    customer_id character varying(32) NOT NULL,
    gender character varying(16) NOT NULL,
    age integer NOT NULL,
    age_group character varying(32) NOT NULL,
    customer_segment character varying(32) NOT NULL,
    CONSTRAINT customers_age_check CHECK (((age >= 0) AND (age <= 120)))
);


--
-- Name: dataset_profile; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dataset_profile (
    profile_id bigint NOT NULL,
    run_id bigint,
    table_name character varying(64) NOT NULL,
    column_name character varying(64) NOT NULL,
    missing_count integer NOT NULL,
    missing_rate numeric(8,4) NOT NULL,
    unique_count integer NOT NULL,
    min_value text,
    max_value text,
    issue_count integer DEFAULT 0 NOT NULL,
    anomaly_count integer DEFAULT 0 NOT NULL,
    invalid_count integer DEFAULT 0 NOT NULL,
    profiled_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: dataset_profile_profile_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dataset_profile_profile_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dataset_profile_profile_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dataset_profile_profile_id_seq OWNED BY public.dataset_profile.profile_id;


--
-- Name: detected_issues; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.detected_issues (
    issue_id character varying(64) NOT NULL,
    run_id bigint,
    row_id character varying(32) NOT NULL,
    table_name character varying(64) NOT NULL,
    column_name character varying(64) NOT NULL,
    issue_type character varying(16) NOT NULL,
    current_value text,
    suggested_value text,
    confidence numeric(6,4),
    severity character varying(16),
    severity_score numeric(6,4),
    reason text,
    source_method character varying(64),
    recommended_action character varying(32),
    can_auto_fix boolean DEFAULT false NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: final_report; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.final_report (
    metric text,
    value double precision
);


--
-- Name: fix_recommendations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.fix_recommendations (
    recommendation_id bigint NOT NULL,
    issue_id character varying(64) NOT NULL,
    row_id character varying(32) NOT NULL,
    table_name character varying(64) NOT NULL,
    column_name character varying(64) NOT NULL,
    suggested_value text,
    confidence numeric(6,4),
    approved boolean DEFAULT false NOT NULL,
    applied_at timestamp without time zone
);


--
-- Name: fix_recommendations_recommendation_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.fix_recommendations_recommendation_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: fix_recommendations_recommendation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.fix_recommendations_recommendation_id_seq OWNED BY public.fix_recommendations.recommendation_id;


--
-- Name: fixed_transactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.fixed_transactions (
    invoice_no character varying(32) NOT NULL,
    customer_id character varying(32) NOT NULL,
    product_id bigint NOT NULL,
    mall_id bigint NOT NULL,
    quantity integer NOT NULL,
    price numeric(12,2) NOT NULL,
    payment_method character varying(32) NOT NULL,
    invoice_date date NOT NULL,
    unit_price numeric(12,2),
    invoice_year integer NOT NULL,
    invoice_month integer NOT NULL,
    invoice_day integer NOT NULL,
    day_of_week integer NOT NULL,
    is_weekend boolean NOT NULL,
    quantity_band character varying(16),
    price_deviation_from_category numeric(12,2),
    fixed_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fixed_transactions_day_of_week_check CHECK (((day_of_week >= 0) AND (day_of_week <= 6))),
    CONSTRAINT fixed_transactions_invoice_day_check CHECK (((invoice_day >= 1) AND (invoice_day <= 31))),
    CONSTRAINT fixed_transactions_invoice_month_check CHECK (((invoice_month >= 1) AND (invoice_month <= 12))),
    CONSTRAINT fixed_transactions_price_check CHECK ((price >= (0)::numeric)),
    CONSTRAINT fixed_transactions_quantity_check CHECK ((quantity >= 1))
);


--
-- Name: products; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.products (
    product_id bigint NOT NULL,
    category character varying(64) NOT NULL,
    base_unit_price numeric(12,2),
    price_band character varying(16)
);


--
-- Name: products_product_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.products_product_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: products_product_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.products_product_id_seq OWNED BY public.products.product_id;


--
-- Name: shopping_malls; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.shopping_malls (
    mall_id bigint NOT NULL,
    shopping_mall character varying(128) NOT NULL,
    mall_tier character varying(16),
    mall_popularity_score numeric(8,4)
);


--
-- Name: shopping_malls_mall_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.shopping_malls_mall_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: shopping_malls_mall_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.shopping_malls_mall_id_seq OWNED BY public.shopping_malls.mall_id;


--
-- Name: staging_customer_shopping_raw; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.staging_customer_shopping_raw (
    row_number bigint NOT NULL,
    invoice_no text,
    customer_id text,
    gender text,
    age text,
    category text,
    quantity text,
    price text,
    payment_method text,
    invoice_date text,
    shopping_mall text,
    source_file character varying(255),
    imported_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: staging_customer_shopping_raw_row_number_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.staging_customer_shopping_raw_row_number_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: staging_customer_shopping_raw_row_number_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.staging_customer_shopping_raw_row_number_seq OWNED BY public.staging_customer_shopping_raw.row_number;


--
-- Name: transactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transactions (
    invoice_no character varying(32) NOT NULL,
    customer_id character varying(32) NOT NULL,
    product_id bigint NOT NULL,
    mall_id bigint NOT NULL,
    quantity integer NOT NULL,
    price numeric(12,2) NOT NULL,
    payment_method character varying(32) NOT NULL,
    invoice_date date NOT NULL,
    unit_price numeric(12,2),
    invoice_year integer NOT NULL,
    invoice_month integer NOT NULL,
    invoice_day integer NOT NULL,
    day_of_week integer NOT NULL,
    is_weekend boolean NOT NULL,
    quantity_band character varying(16),
    price_deviation_from_category numeric(12,2),
    CONSTRAINT transactions_day_of_week_check CHECK (((day_of_week >= 0) AND (day_of_week <= 6))),
    CONSTRAINT transactions_invoice_day_check CHECK (((invoice_day >= 1) AND (invoice_day <= 31))),
    CONSTRAINT transactions_invoice_month_check CHECK (((invoice_month >= 1) AND (invoice_month <= 12))),
    CONSTRAINT transactions_price_check CHECK ((price >= (0)::numeric)),
    CONSTRAINT transactions_quantity_check CHECK ((quantity >= 1))
);


--
-- Name: cleaning_actions action_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cleaning_actions ALTER COLUMN action_id SET DEFAULT nextval('public.cleaning_actions_action_id_seq'::regclass);


--
-- Name: cleaning_runs run_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cleaning_runs ALTER COLUMN run_id SET DEFAULT nextval('public.cleaning_runs_run_id_seq'::regclass);


--
-- Name: dataset_profile profile_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dataset_profile ALTER COLUMN profile_id SET DEFAULT nextval('public.dataset_profile_profile_id_seq'::regclass);


--
-- Name: fix_recommendations recommendation_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fix_recommendations ALTER COLUMN recommendation_id SET DEFAULT nextval('public.fix_recommendations_recommendation_id_seq'::regclass);


--
-- Name: products product_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products ALTER COLUMN product_id SET DEFAULT nextval('public.products_product_id_seq'::regclass);


--
-- Name: shopping_malls mall_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shopping_malls ALTER COLUMN mall_id SET DEFAULT nextval('public.shopping_malls_mall_id_seq'::regclass);


--
-- Name: staging_customer_shopping_raw row_number; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.staging_customer_shopping_raw ALTER COLUMN row_number SET DEFAULT nextval('public.staging_customer_shopping_raw_row_number_seq'::regclass);


--
-- Name: cleaning_actions cleaning_actions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cleaning_actions
    ADD CONSTRAINT cleaning_actions_pkey PRIMARY KEY (action_id);


--
-- Name: cleaning_runs cleaning_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cleaning_runs
    ADD CONSTRAINT cleaning_runs_pkey PRIMARY KEY (run_id);


--
-- Name: customers customers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_pkey PRIMARY KEY (customer_id);


--
-- Name: dataset_profile dataset_profile_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dataset_profile
    ADD CONSTRAINT dataset_profile_pkey PRIMARY KEY (profile_id);


--
-- Name: detected_issues detected_issues_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.detected_issues
    ADD CONSTRAINT detected_issues_pkey PRIMARY KEY (issue_id);


--
-- Name: fix_recommendations fix_recommendations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fix_recommendations
    ADD CONSTRAINT fix_recommendations_pkey PRIMARY KEY (recommendation_id);


--
-- Name: fixed_transactions fixed_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fixed_transactions
    ADD CONSTRAINT fixed_transactions_pkey PRIMARY KEY (invoice_no);


--
-- Name: products products_category_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_category_key UNIQUE (category);


--
-- Name: products products_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (product_id);


--
-- Name: shopping_malls shopping_malls_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shopping_malls
    ADD CONSTRAINT shopping_malls_pkey PRIMARY KEY (mall_id);


--
-- Name: shopping_malls shopping_malls_shopping_mall_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shopping_malls
    ADD CONSTRAINT shopping_malls_shopping_mall_key UNIQUE (shopping_mall);


--
-- Name: staging_customer_shopping_raw staging_customer_shopping_raw_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.staging_customer_shopping_raw
    ADD CONSTRAINT staging_customer_shopping_raw_pkey PRIMARY KEY (row_number);


--
-- Name: transactions transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_pkey PRIMARY KEY (invoice_no);


--
-- Name: idx_detected_issues_row_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_detected_issues_row_id ON public.detected_issues USING btree (row_id);


--
-- Name: idx_detected_issues_run_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_detected_issues_run_id ON public.detected_issues USING btree (run_id);


--
-- Name: idx_transactions_customer_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transactions_customer_id ON public.transactions USING btree (customer_id);


--
-- Name: idx_transactions_invoice_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transactions_invoice_date ON public.transactions USING btree (invoice_date);


--
-- Name: idx_transactions_mall_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transactions_mall_id ON public.transactions USING btree (mall_id);


--
-- Name: idx_transactions_payment_method; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transactions_payment_method ON public.transactions USING btree (payment_method);


--
-- Name: idx_transactions_product_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transactions_product_id ON public.transactions USING btree (product_id);


--
-- Name: cleaning_actions cleaning_actions_issue_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cleaning_actions
    ADD CONSTRAINT cleaning_actions_issue_id_fkey FOREIGN KEY (issue_id) REFERENCES public.detected_issues(issue_id);


--
-- Name: dataset_profile dataset_profile_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dataset_profile
    ADD CONSTRAINT dataset_profile_run_id_fkey FOREIGN KEY (run_id) REFERENCES public.cleaning_runs(run_id);


--
-- Name: detected_issues detected_issues_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.detected_issues
    ADD CONSTRAINT detected_issues_run_id_fkey FOREIGN KEY (run_id) REFERENCES public.cleaning_runs(run_id);


--
-- Name: fix_recommendations fix_recommendations_issue_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fix_recommendations
    ADD CONSTRAINT fix_recommendations_issue_id_fkey FOREIGN KEY (issue_id) REFERENCES public.detected_issues(issue_id);


--
-- Name: fixed_transactions fixed_transactions_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fixed_transactions
    ADD CONSTRAINT fixed_transactions_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(customer_id);


--
-- Name: fixed_transactions fixed_transactions_invoice_no_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fixed_transactions
    ADD CONSTRAINT fixed_transactions_invoice_no_fkey FOREIGN KEY (invoice_no) REFERENCES public.transactions(invoice_no);


--
-- Name: fixed_transactions fixed_transactions_mall_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fixed_transactions
    ADD CONSTRAINT fixed_transactions_mall_id_fkey FOREIGN KEY (mall_id) REFERENCES public.shopping_malls(mall_id);


--
-- Name: fixed_transactions fixed_transactions_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fixed_transactions
    ADD CONSTRAINT fixed_transactions_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(product_id);


--
-- Name: transactions transactions_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(customer_id);


--
-- Name: transactions transactions_mall_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_mall_id_fkey FOREIGN KEY (mall_id) REFERENCES public.shopping_malls(mall_id);


--
-- Name: transactions transactions_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(product_id);


--
-- PostgreSQL database dump complete
--

\unrestrict n20G6BbsIEzTZM7jHfbOUcAWZFAydch6efTbqbdPs38uLa3xDQGH0b8NN4oCEFd

