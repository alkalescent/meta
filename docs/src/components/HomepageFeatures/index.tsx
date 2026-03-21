import type {ReactNode} from 'react';
import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

type FeatureItem = {
  title: string;
  icon: string;
  description: ReactNode;
};

const FeatureList: FeatureItem[] = [
  {
    title: 'Instant Detection',
    icon: '🔍',
    description: (
      <>
        Drop into any codebase and meta detects its type, framework, and
        language from marker files alone — no configuration required.
      </>
    ),
  },
  {
    title: 'Full Visibility',
    icon: '📦',
    description: (
      <>
        See dependencies, scripts, and environment variables at a glance —
        across Node.js, Python, Rust, Go, Ruby, PHP, and more.
      </>
    ),
  },
  {
    title: 'Health Checks',
    icon: '✓',
    description: (
      <>
        Catch missing lockfiles, stale READMEs, leaked secrets, and missing
        CI config before they become someone else's problem.
      </>
    ),
  },
];

function Feature({title, icon, description}: FeatureItem) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        <span className={styles.featureIcon} role="img" aria-hidden="true">
          {icon}
        </span>
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures(): ReactNode {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
